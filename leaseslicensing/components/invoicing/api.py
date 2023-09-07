import logging
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from ledger_api_client import utils as ledger_api_client_utils
from ledger_api_client.utils import generate_payment_session
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_datatables.filters import DatatablesFilterBackend

from leaseslicensing.components.approvals.serializers import ApprovalSerializer
from leaseslicensing.components.invoicing.email import (
    send_invoice_paid_external_notification,
    send_invoice_paid_internal_notification,
    send_new_invoice_raised_internal_notification,
    send_new_invoice_raised_notification,
)
from leaseslicensing.components.invoicing.models import (
    CPICalculationMethod,
    Invoice,
    InvoiceTransaction,
    InvoicingDetails,
)
from leaseslicensing.components.invoicing.serializers import (
    CPICalculationMethodSerializer,
    InvoiceEditOracleInvoiceNumberSerializer,
    InvoiceSerializer,
    InvoiceTransactionSerializer,
    InvoicingDetailsSerializer,
)
from leaseslicensing.components.main.api import LicensingViewset, NoPaginationListMixin
from leaseslicensing.components.organisations.models import (
    Organisation,
    OrganisationContact,
)
from leaseslicensing.components.organisations.utils import get_organisation_ids_for_user
from leaseslicensing.helpers import gst_from_total, is_customer, is_finance_officer
from leaseslicensing.ledger_api_utils import retrieve_email_user
from leaseslicensing.permissions import IsFinanceOfficer

logger = logging.getLogger(__name__)


class InvoiceFilterBackend(DatatablesFilterBackend):
    def filter_queryset(self, request, queryset, view):
        approval_id = request.GET.get("approval_id", None)
        if approval_id:
            queryset = queryset.filter(approval_id=approval_id)

        total_count = queryset.count()

        filter_invoice_organisation = (
            request.GET.get("filter_invoice_organisation")
            if request.GET.get("filter_invoice_organisation") != "all"
            else ""
        )
        filter_invoice_status = (
            request.GET.get("filter_invoice_status")
            if request.GET.get("filter_invoice_status") != "all"
            else ""
        )
        filter_invoice_due_date_from = request.GET.get("filter_invoice_due_date_from")
        filter_invoice_due_date_to = request.GET.get("filter_invoice_due_date_to")

        if filter_invoice_organisation:
            queryset = queryset.filter(
                approval__current_proposal__org_applicant=filter_invoice_organisation
            )

        if filter_invoice_status:
            if "overdue" == filter_invoice_status:
                queryset = queryset.filter(
                    status=Invoice.INVOICE_STATUS_UNPAID,
                    date_due__lte=datetime.now().date(),
                )
            else:
                queryset = queryset.filter(status=filter_invoice_status)

        if filter_invoice_due_date_from:
            filter_invoice_due_date_from = datetime.strptime(
                filter_invoice_due_date_from, "%Y-%m-%d"
            )
            queryset = queryset.filter(date_due__gte=filter_invoice_due_date_from)

        if filter_invoice_due_date_to:
            filter_invoice_due_date_to = datetime.strptime(
                filter_invoice_due_date_to, "%Y-%m-%d"
            )
            queryset = queryset.filter(date_due__lte=filter_invoice_due_date_to)

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        queryset = queryset.order_by(*ordering)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, "_datatables_filtered_count", queryset.count())
        setattr(view, "_datatables_total_count", total_count)

        return queryset


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [InvoiceFilterBackend]
    search_fields = ["lodgement_number", "oracle_invoice_number"]

    def get_queryset(self):
        if is_customer(self.request):
            org_ids = get_organisation_ids_for_user(self.request.user.id)
            return (
                super()
                .get_queryset()
                .exclude(status=Invoice.INVOICE_STATUS_PENDING_UPLOAD_ORACLE_INVOICE)
                .exclude(invoice_pdf="")
                .exclude(oracle_invoice_number__isnull=True)
                .filter(
                    Q(approval__current_proposal__ind_applicant=self.request.user.id)
                    | Q(approval__current_proposal__org_applicant__in=org_ids)
                )
            )
        return super().get_queryset()

    @action(detail=False, methods=["get"])
    def statuses(self, request, *args, **kwargs):
        return Response(
            [
                {"id": status[0], "name": status[1]}
                for status in Invoice.INVOICE_STATUS_CHOICES
            ]
        )

    @action(detail=True, methods=["get"])
    def transactions(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = InvoiceTransactionSerializer(
            instance.transactions.all(), many=True
        )
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def record_transaction(self, request, *args, **kwargs):
        if not is_finance_officer(request):
            return Response(
                {
                    "message": "You do not have permission to record an invoice transaction"
                }
            )

        instance = self.get_object()

        credit = request.data.get("credit", Decimal("0.00"))
        debit = request.data.get("debit", Decimal("0.00"))

        serializer = InvoiceTransactionSerializer(
            data={
                "invoice": instance.id,
                "credit": credit,
                "debit": debit,
            }
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        invoice_transaction = serializer.save()

        if Decimal("0.00") == invoice_transaction.invoice.balance:
            invoice_transaction.invoice.status = Invoice.INVOICE_STATUS_PAID
            invoice_transaction.invoice.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    def generate_ad_hoc_invoice(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.ad_hoc = True
        instance.gst_free = instance.approval.approval_type.gst_free
        instance.save()
        # Todo: Send oracle invoice and oracle invoice number to ledger
        # send emails etc.
        return Response(serializer.data)

    @action(detail=True, methods=["PATCH"])
    @transaction.atomic
    def upload_oracle_invoice(self, request, *args, **kwargs):
        if not is_finance_officer(request):
            return Response(
                {"message": "You do not have permission to upload an Oracle Invoice"}
            )

        instance = self.get_object()

        # Once the finance user has uploaded an oracle invoice and entered the oracle invoice number
        # we can set the issue date and due date
        date_issued = timezone.now()
        date_due = date_issued + timezone.timedelta(
            days=settings.DEFAULT_DAYS_BEFORE_PAYMENT_DUE
        )

        data = request.data.copy()
        data.update(
            {
                "status": Invoice.INVOICE_STATUS_UNPAID,
                "date_issued": date_issued,
                "date_due": date_due,
            }
        )

        serializer = InvoiceEditOracleInvoiceNumberSerializer(instance, data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        serializer.save()
        logger.info(f"Oracle Invoice uploaded for Invoice: {instance.lodgement_number}")

        # Create the 'future' ledger invoice
        logger.info(
            f"Creating future ledger invoice for Invoice: {instance.lodgement_number}"
        )
        approval = instance.approval

        description = (
            f"{approval.approval_type} {approval.lodgement_number}: "
            f"{approval.invoicing_details.charge_method}"
        )

        price_incl_tax = instance.amount
        price_excl_tax = instance.amount

        if not approval.approval_type.gst_free:
            price_excl_tax = price_incl_tax - gst_from_total(price_incl_tax)

        ledger_order_lines = []

        ledger_order_lines.append(
            {
                "ledger_description": description,
                "quantity": 1,
                "price_excl_tax": str(
                    price_excl_tax
                ),  # Todo gst applies for leases but not for licences
                "price_incl_tax": str(price_incl_tax),
                "oracle_code": "Todo: Get Oracle Code",
                "line_status": settings.LEDGER_DEFAULT_LINE_STATUS,
            },
        )
        logger.info(
            f"Setting ledger order lines {ledger_order_lines} for Invoice: {instance.lodgement_number}"
        )

        # We need a fake request as we are adding the proponent as the request.user
        fake_request = ledger_api_client_utils.FakeRequestSessionObj()

        basket_params = {
            "products": ledger_order_lines,
            "vouchers": [],
            "system": settings.PAYMENT_SYSTEM_ID,
            "tax_override": True,
            "custom_basket": True,
            "booking_reference": str(instance.lodgement_number),
            "no_payment": True,
        }
        logger.info(
            f"Setting basket parameters: {basket_params} for Invoice: {instance.lodgement_number}"
        )

        if type(approval.applicant) == Organisation:
            organisation = approval.applicant
            basket_params["organisation"] = organisation.ledger_organisation_id
            admin_contact = organisation.contacts.filter(
                user_role=OrganisationContact.USER_ROLE_CHOICE_ADMIN,
                user_status=OrganisationContact.USER_STATUS_CHOICE_ACTIVE,
            ).first()
            if not admin_contact:
                logger.error(
                    f"Unable to retrieve admin contact for organisation: {organisation}"
                )
                return
            fake_request.user = retrieve_email_user(admin_contact.user)
        else:
            fake_request.user = approval.applicant

        logger.info(
            f"Setting request user {fake_request.user} for Invoice: {instance.lodgement_number}"
        )

        logger.info(f"Creating basket session for Invoice: {instance.lodgement_number}")
        basket_hash = ledger_api_client_utils.create_basket_session(
            fake_request, fake_request.user.id, basket_params
        )
        basket_hash = basket_hash.split("|")[0]
        invoice_text = f"Leases Licensing Invoice {instance.lodgement_number}"
        if approval.current_proposal.proponent_reference_number:
            invoice_text += f"(Proponent Ref: {approval.current_proposal.proponent_reference_number})"
        return_preload_url = (
            f"{settings.LEASES_LICENSING_EXTERNAL_URL}"
            f"/api/invoicing/ledger-api-invoice-success-callback/{instance.uuid}"
        )

        logger.info(f"Creating future invoice for Invoice: {instance.lodgement_number}")
        future_invoice = ledger_api_client_utils.process_create_future_invoice(
            basket_hash, invoice_text, return_preload_url
        )

        if 200 != future_invoice["status"]:
            logger.error(
                f"Failed to create future Invoice {instance.lodgement_number} with basket_hash "
                f"{basket_hash}, invoice_text {invoice_text}, return_preload_url {return_preload_url}"
            )
            return

        logger.debug(f"Future invoice created for Invoice: {instance}")

        data = future_invoice["data"]
        instance.order_number = data["order"]
        instance.basket_id = data["basket_id"]
        instance.invoice_reference = data["invoice"]
        instance.save()

        # Send request for payment to proponent
        send_new_invoice_raised_notification(approval, instance)

        return Response(serializer.data)

    @action(methods=["GET"], detail=True)
    def pay_invoice(self, request, *args, **kwargs):
        logger.info("Pay Invoice")
        invoice = self.get_object()
        return_url = reverse(
            "external-pay-invoice-success",
            kwargs={"id": invoice.id},
        )
        fallback_url = reverse(
            "external-pay-invoice-failure",
            kwargs={"id": invoice.id},
        )

        logger.info(f"Return URL: {request.build_absolute_uri(return_url)}")
        logger.info(f"Fallback URL: {fallback_url}")
        payment_session = generate_payment_session(
            request,
            invoice.invoice_reference,
            request.build_absolute_uri(return_url),
            request.build_absolute_uri(fallback_url),
        )
        logger.info(f"Payment session: {payment_session}")

        if 200 == payment_session["status"]:
            return redirect(reverse("ledgergw-payment-details"))

        return redirect(fallback_url)

    @action(
        methods=["GET"],
        detail=True,
    )
    def retrieve_invoice_receipt(self, request, *args, **kwargs):
        instance = self.get_object()
        invoice_url = instance.ledger_invoice_url
        if invoice_url:
            response = requests.get(invoice_url)
            return FileResponse(response, content_type="application/pdf")

        raise Http404


class InvoiceTransactionViewSet(viewsets.ModelViewSet):
    queryset = InvoiceTransaction.objects.all()
    serializer_class = InvoiceTransactionSerializer


class CPICalculationMethodViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet, NoPaginationListMixin
):
    queryset = CPICalculationMethod.objects.filter(archived=False)
    serializer_class = CPICalculationMethodSerializer


class PayInvoiceSuccessCallbackView(APIView):
    throttle_classes = [AnonRateThrottle]

    @transaction.atomic
    def get(self, request, uuid, format=None):
        logger.info("Leases Licensing Pay Invoice Success View get method called.")

        if (
            uuid
            and Invoice.objects.filter(
                uuid=uuid, status=Invoice.INVOICE_STATUS_UNPAID
            ).exists()
        ):
            logger.info(
                f"Invoice uuid: {uuid}.",
            )
            invoice = Invoice.objects.get(uuid=uuid)

            InvoiceTransaction.objects.create(
                invoice=invoice,
                debit=invoice.amount,
            )

            invoice.status = Invoice.INVOICE_STATUS_PAID
            invoice.date_paid = timezone.now()
            invoice.save()

            send_invoice_paid_external_notification(invoice)

            send_invoice_paid_internal_notification(invoice)

            logger.info(
                "Returning status.HTTP_200_OK. Invoice marked as paid successfully.",
            )
            # this end-point is called by an unmonitored get request in ledger so there is no point having a
            # a response body however we will return a status in case this is used on the ledger end in future
            return Response(status=status.HTTP_200_OK)

        # If there is no uuid to identify the cart then send a bad request status back in case ledger can
        # do something with this in future
        logger.info(
            "Returning status.HTTP_400_BAD_REQUEST bad request as there "
            f"was not an unpaid invoice with uuid: {uuid}."
        )
        return Response(status=status.HTTP_400_BAD_REQUEST)


class InvoicingDetailsViewSet(LicensingViewset):
    queryset = InvoicingDetails.objects.all()
    serializer_class = InvoicingDetailsSerializer
    permission_classes = [IsFinanceOfficer]

    @action(methods=["PUT"], detail=True)
    def update_and_preview_invoices(self, request, *args, **kwargs):
        # Save any changes made to the invoicing details
        self.update(request, *args, **kwargs)
        return self.preview_invoices(request, *args, **kwargs)

    @action(methods=["GET"], detail=True)
    def preview_invoices(self, request, *args, **kwargs):
        return Response(self.get_object().preview_invoices)

    @action(methods=["PUT"], detail=True)
    def complete_editing(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check for any changes made to the gross turnover amounts for financial quarters
        self.process_gross_turnover_changes(instance, request.data)

        self.update(request, *args, **kwargs)
        instance.approval.status = instance.approval.APPROVAL_STATUS_CURRENT
        instance.approval.save(version_comment="Completed Editing Invoicing Details")
        serializer = ApprovalSerializer(instance.approval, context={"request": request})
        return Response(serializer.data)

    def process_gross_turnover_changes(self, instance, data):
        """When the finance group user enters amounts for financial quarters and years
        the system"""
        annual_gross_turnover_changes = []
        quarterly_gross_turnover_changes = []
        new_gross_turnover = None
        new_gross_turnover_percentages = data.get("gross_turnover_percentages")
        gross_turnover_percentages = list(instance.gross_turnover_percentages.all())
        for i, gross_turnover_percentage in enumerate(gross_turnover_percentages):
            if not new_gross_turnover_percentages[i]:
                continue

            new_gross_turnover = None
            if new_gross_turnover_percentages[i]["gross_turnover"]:
                new_gross_turnover = Decimal(
                    new_gross_turnover_percentages[i]["gross_turnover"]
                ).quantize(Decimal("0.01"))

            if new_gross_turnover != gross_turnover_percentage.gross_turnover:
                annual_gross_turnover_changes.append(new_gross_turnover_percentages[i])

            quarters = list(gross_turnover_percentage.quarters.all())
            new_quarters = new_gross_turnover_percentages[i].get("quarters")
            for j, quarter in enumerate(quarters):
                if not new_quarters[j]:
                    continue

                if not new_quarters[j]["gross_turnover"]:
                    continue

                new_gross_turnover = Decimal(
                    new_quarters[j]["gross_turnover"]
                ).quantize(Decimal("0.01"))
                if new_gross_turnover != quarter.gross_turnover:
                    new_quarters[j]["percentage"] = Decimal(
                        new_gross_turnover_percentages[i]["percentage"]
                    ).quantize(Decimal("0.01"))
                    quarterly_gross_turnover_changes.append(new_quarters[j])

        gst_free = instance.approval.approval_type.gst_free

        # Raise an invoice for each quarterly gross turnover entered
        for quarterly_gross_turnover_change in quarterly_gross_turnover_changes:
            percentage = quarterly_gross_turnover_change["percentage"]
            amount = quarterly_gross_turnover_change["gross_turnover"] * (
                percentage / 100
            )
            invoice = Invoice.objects.create(
                approval=instance.approval, amount=amount, gst_free=gst_free
            )

            # Send email to notify finance group users
            send_new_invoice_raised_internal_notification(instance.approval, invoice)

        # For annual gross turnover amounts, check if there is a discrepancy between the
        # total of the quarters and the annual amount. If there is, raise an invoice for the difference
        for annual_gross_turnover_change in annual_gross_turnover_changes:
            total_of_quarters = sum(
                [
                    quarter["gross_turnover"]
                    for quarter in annual_gross_turnover_change["quarters"]
                ]
            )
            if annual_gross_turnover_change["gross_turnover"] != total_of_quarters:
                difference = (
                    annual_gross_turnover_change["gross_turnover"] - total_of_quarters
                )
                amount = difference * (percentage / 100)
                invoice = Invoice.objects.create(
                    approval=instance.approval, amount=amount, gst_free=gst_free
                )

                # Send email to notify finance group users
                send_new_invoice_raised_internal_notification(
                    instance.approval, invoice
                )
