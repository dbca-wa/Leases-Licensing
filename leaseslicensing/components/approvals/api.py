import logging
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import CharField, F, Q, Value
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers, views, viewsets
from rest_framework.decorators import action as detail_route
from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.renderers import DatatablesRenderer
from reversion.errors import RevertError
from reversion.models import Version

from leaseslicensing.components.approvals.document import ApprovalDocumentGenerator
from leaseslicensing.components.approvals.models import (
    Approval,
    ApprovalDocument,
    ApprovalTransfer,
    ApprovalTransferApplicant,
    ApprovalType,
)
from leaseslicensing.components.approvals.serializers import (
    ApprovalCancellationSerializer,
    ApprovalHistorySerializer,
    ApprovalKeyValueSerializer,
    ApprovalLogEntrySerializer,
    ApprovalSerializer,
    ApprovalSurrenderSerializer,
    ApprovalSuspensionSerializer,
    ApprovalTransferSerializer,
    ApprovalUserActionSerializer,
)
from leaseslicensing.components.compliances.models import Compliance
from leaseslicensing.components.invoicing.serializers import InvoiceSerializer
from leaseslicensing.components.main.api import (
    KeyValueListMixin,
    LicensingViewSet,
    UserActionLoggingViewset,
)
from leaseslicensing.components.main.decorators import basic_exception_handler
from leaseslicensing.components.main.process_document import process_generic_document
from leaseslicensing.components.main.serializers import RelatedItemSerializer
from leaseslicensing.components.organisations.utils import get_organisation_ids_for_user
from leaseslicensing.components.proposals.api import ProposalRenderer
from leaseslicensing.components.proposals.models import ApplicationType, Proposal
from leaseslicensing.helpers import is_assessor, is_customer, is_internal
from leaseslicensing.permissions import (
    HasObjectPermission,
    IsAssessor,
    IsFinanceOfficer,
)

logger = logging.getLogger(__name__)


class GetApprovalTypesDict(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        document_generator = ApprovalDocumentGenerator()
        approval_types_dict = cache.get(settings.CACHE_KEY_APPROVAL_TYPES_DICTIONARY)
        if not approval_types_dict:
            approval_types_dict = [
                {
                    "id": t.id,
                    "name": t.name,
                    "details_placeholder": t.details_placeholder,
                    "approval_type_document_types": [
                        {
                            "id": doc_type_link.approval_type_document_type.id,
                            "name": doc_type_link.approval_type_document_type.name,
                            "mandatory": doc_type_link.mandatory,
                            "has_template": document_generator.has_template(
                                t.name, doc_type_link.approval_type_document_type.name
                            ),
                        }
                        # for doc_type in t.approvaltypedocumenttypes.all()
                        for doc_type_link in t.approvaltype_approvaltypedocumenttypes.all()
                    ],
                }
                for t in ApprovalType.objects.all()
            ]
            cache.set(
                settings.CACHE_KEY_APPROVAL_TYPES_DICTIONARY,
                approval_types_dict,
                settings.LOV_CACHE_TIMEOUT,
            )
        return Response(approval_types_dict)


class GetApprovalStatusesDict(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        approval_statuses = cache.get(settings.CACHE_KEY_APPROVAL_STATUSES)
        if approval_statuses is None:
            approval_statuses = [
                {"code": i[0], "description": i[1]} for i in Approval.STATUS_CHOICES
            ]
            cache.set(
                settings.CACHE_KEY_APPROVAL_STATUSES,
                approval_statuses,
                settings.LOV_CACHE_TIMEOUT,
            )
        return Response(approval_statuses)


class ApprovalFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """

    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        filter_approval_type = (
            request.GET.get("filter_approval_type")
            if request.GET.get("filter_approval_type") != "all"
            else ""
        )
        filter_approval_status = (
            request.GET.get("filter_approval_status")
            if request.GET.get("filter_approval_status") != "all"
            else ""
        )
        filter_approval_expiry_date_from = request.GET.get(
            "filter_approval_expiry_date_from"
        )
        filter_approval_expiry_date_to = request.GET.get(
            "filter_approval_expiry_date_to"
        )

        filter_approval_organisation = (
            request.GET.get("filter_approval_organisation")
            if request.GET.get("filter_approval_organisation") != "all"
            else ""
        )
        filter_approval_region = (
            request.GET.get("filter_approval_region")
            if request.GET.get("filter_approval_region") != "all"
            else ""
        )
        filter_approval_district = (
            request.GET.get("filter_approval_district")
            if request.GET.get("filter_approval_district") != "all"
            else ""
        )
        filter_approval_group = (
            request.GET.get("filter_approval_group")
            if request.GET.get("filter_approval_group") != "all"
            else ""
        )

        if filter_approval_type:
            filter_approval_type = int(filter_approval_type)
            queryset = queryset.filter(approval_type__id=filter_approval_type)

        if filter_approval_status:
            queryset = queryset.filter(status=filter_approval_status)

        if filter_approval_expiry_date_from:
            filter_approval_expiry_date_from = datetime.strptime(
                filter_approval_expiry_date_from, "%Y-%m-%d"
            )
            queryset = queryset.filter(
                expiry_date__gte=filter_approval_expiry_date_from
            )

        if filter_approval_expiry_date_to:
            filter_approval_expiry_date_to = datetime.strptime(
                filter_approval_expiry_date_to, "%Y-%m-%d"
            )
            queryset = queryset.filter(expiry_date__lte=filter_approval_expiry_date_to)

        if filter_approval_organisation:
            filter_approval_organisation = int(filter_approval_organisation)
            queryset = queryset.filter(
                current_proposal__org_applicant_id=filter_approval_organisation
            )

        if filter_approval_region:
            filter_approval_region = int(filter_approval_region)
            queryset = queryset.filter(
                current_proposal__regions__region_id=filter_approval_region
            )
        if filter_approval_district:
            filter_approval_district = int(filter_approval_district)
            queryset = queryset.filter(
                current_proposal__districts__district_id=filter_approval_district
            )
        if filter_approval_group:
            filter_approval_group = int(filter_approval_group)
            queryset = queryset.filter(
                current_proposal__groups__group_id=filter_approval_group
            )

        queryset = super().filter_queryset(request, queryset, view)

        setattr(view, "_datatables_filtered_count", queryset.count())
        setattr(view, "_datatables_total_count", total_count)

        return queryset


class ApprovalPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (ApprovalFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (ProposalRenderer,)
    page_size = 10
    queryset = Approval.objects.none()
    serializer_class = ApprovalSerializer
    permission_classes = [IsAssessor | IsFinanceOfficer | HasObjectPermission]

    def get_queryset(self):
        if not is_internal(self.request) and not is_customer(self.request):
            return super().get_queryset()

        if is_internal(self.request):
            qs = Approval.objects.all()
        elif is_customer(self.request):
            qs = Approval.get_approvals_for_emailuser(self.request.user.id)

        target_email_user_id = self.request.query_params.get(
            "target_email_user_id", None
        )
        if (
            target_email_user_id
            and target_email_user_id.isnumeric()
            and int(target_email_user_id) > 0
        ):
            target_email_user_id = int(target_email_user_id)
            qs = qs.filter(current_proposal__submitter=target_email_user_id)

        target_organisation_id = self.request.query_params.get(
            "target_organisation_id", None
        )
        if (
            target_organisation_id
            and target_organisation_id.isnumeric()
            and int(target_organisation_id) > 0
        ):
            target_organisation_id = int(target_organisation_id)
            qs = qs.exclude(current_proposal__org_applicant__isnull=True).filter(
                current_proposal__org_applicant__id=target_organisation_id
            )

        target_compliance_id = self.request.query_params.get(
            "target_compliance_id", None
        )
        if (
            target_compliance_id
            and target_compliance_id.isnumeric()
            and int(target_compliance_id) > 0
        ):
            compliance = Compliance.objects.get(id=target_compliance_id)

            qs = qs.filter(id=compliance.approval_id)

        return qs

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def approvals_external(self, request, *args, **kwargs):
        """
        Paginated serializer for datatables - used by the internal and external dashboard
        (filtered by the get_queryset method)

        To test:
            http://localhost:8000/api/approval_paginated/approvals_external/?format=datatables&draw=1&length=2
        """
        ids = (
            self.get_queryset()
            .order_by("lodgement_number", "-issue_date")
            .distinct("lodgement_number")
            .values_list("id", flat=True)
        )
        qs = Approval.objects.filter(id__in=ids)
        qs = self.filter_queryset(qs)

        # on the internal organisations dashboard, filter the Proposal/Approval/Compliance datatables
        # by applicant/organisation
        applicant_id = request.GET.get("org_id")
        if applicant_id:
            qs = qs.filter(org_applicant_id=applicant_id)
        submitter_id = request.GET.get("submitter_id", None)
        if submitter_id:
            qs = qs.filter(submitter_id=submitter_id)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ApprovalSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)


class ApprovalViewSet(UserActionLoggingViewset, KeyValueListMixin):
    queryset = Approval.objects.none()
    serializer_class = ApprovalSerializer
    pagination_class = DatatablesPageNumberPagination
    key_value_display_field = "lodgement_number"
    key_value_serializer_class = ApprovalKeyValueSerializer
    permission_classes = [IsAssessor | IsFinanceOfficer | HasObjectPermission]

    def get_queryset(self):
        if is_internal(self.request):
            return Approval.objects.all()
        elif is_customer(self.request):
            user_orgs = get_organisation_ids_for_user(self.request.user.id)
            queryset = Approval.objects.filter(
                Q(current_proposal__org_applicant_id__in=user_orgs)
                | Q(current_proposal__ind_applicant=self.request.user.id)
            )
            return queryset
        return Approval.objects.none()

    def list(self, request, *args, **kwargs):
        # queryset = self.get_queryset()
        queryset = (
            self.get_queryset()
            .order_by("lodgement_number", "-issue_date")
            .distinct("lodgement_number")
        )
        # Filter by org
        org_id = request.GET.get("org_id", None)
        if org_id:
            queryset = queryset.filter(org_applicant_id=org_id)
        submitter_id = request.GET.get("submitter_id", None)
        if submitter_id:
            queryset = queryset.filter(submitter_id=submitter_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def filter_list(self, request, *args, **kwargs):
        """Used by the external dashboard filters"""
        # region_qs =  self.get_queryset().filter(current_proposal__region__isnull=False)
        # .values_list('current_proposal__region__name', flat=True).distinct()
        # activity_qs =  self.get_queryset().filter(current_proposal__activity__isnull=False)
        # .values_list('current_proposal__activity', flat=True).distinct()
        application_types = ApplicationType.objects.all().values_list("name", flat=True)
        data = dict(
            approval_status_choices=[i[1] for i in Approval.STATUS_CHOICES],
            application_types=application_types,
        )
        return Response(data)

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_approval_cancellation_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="approval_cancellation_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_approval_surrender_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="approval_surrender_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_approval_suspension_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="approval_suspension_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def approval_cancellation(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ApprovalCancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.approval_cancellation(request, serializer.validated_data)
        serializer = ApprovalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def approval_suspension(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ApprovalSuspensionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.approval_suspension(request, serializer.validated_data)
        serializer = ApprovalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def approval_reinstate(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.reinstate_approval(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def approval_surrender(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ApprovalSurrenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.approval_surrender(request, serializer.validated_data)
        serializer = ApprovalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def review_renewal(self, request, *args, **kwargs):
        if not is_assessor(request):
            raise serializers.ValidationError(
                "You do not have permission to perform this action."
            )

        instance = self.get_object()

        can_be_renewed = request.data.get("can_be_renewed", None)
        if can_be_renewed is None:
            raise serializers.ValidationError(
                "Expecting a boolean value can_be_renewed in POST"
            )

        instance.review_renewal(can_be_renewed)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    @basic_exception_handler
    def review_invoice_details(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = Approval.APPROVAL_STATUS_CURRENT_EDITING_INVOICING
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    @basic_exception_handler
    def cancel_editing_invoicing(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = Approval.APPROVAL_STATUS_CURRENT
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def approval_history(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.licence_document:
            logger.warning(f"No license document found for approval {instance}")
            return Response({})

        versions = Version.objects.get_for_object(instance)

        first = versions.first()
        if not first:
            return Response({})

        versions = versions.filter(
            ~Q(revision__comment="")
            # | Q(revision_id=first.revision_id)
        ).order_by("-revision__date_created")

        approvals = []  # List of history approvals to return
        # List to make sure there is only one approval (the most recent one) per lodgement number and lodgement sequence
        # Can have a new approval of a different lodgement number show up in the version history after renewing and approval
        lodgement_sequences = {}
        for version in versions:
            version_set = version.revision.version_set.all()

            approval = None
            documents = []
            revision_comment = ""
            for vs in version_set:
                revision_comment = vs.revision.comment
                if revision_comment.startswith("New Approval document"):
                    continue
                try:
                    obj_class = vs._object_version.object.__class__
                except RevertError:
                    logger.exception("Error reverting object version")
                    continue
                if obj_class == Approval:
                    approval = vs._object_version.object
                elif obj_class == ApprovalDocument:
                    documents.append(vs._object_version.object)

            if not approval:
                continue
            if not approval.id in lodgement_sequences:
                lodgement_sequences[approval.id] = []
            if approval.lodgement_sequence in lodgement_sequences[approval.id]:
                # Don't add to the history when there is no approval
                # or when the lodgement sequence is already in the list
                continue
            lodgement_sequences[approval.id].append(approval.lodgement_sequence)

            for doc in documents:
                if doc.id == approval.licence_document_id:
                    approval.licence_document = doc
                if doc.id == approval.cover_letter_document_id:
                    approval.cover_letter_document = doc

            approval.revision_id = version.revision_id
            approval.version_date = version.revision.date_created
            approval.revision_comment = revision_comment

            version_date = version.revision.date_created.strftime(
                "%d/%m/%Y %I:%M:%S %p"
            )
            logger.info(
                f"Adding approval {approval}-{approval.lodgement_sequence} from {version_date} to history table"
            )
            approvals.append(approval)

        # Comma separated list of approvals for logging
        approvals_str = ", ".join(
            [
                f"Approval:{ln}-{ls}"
                for ln in lodgement_sequences
                for ls in lodgement_sequences[ln]
            ]
        )
        logger.info(f"Returning Approval history: {approvals_str}")
        # Sort by id first, then by lodgement sequence (don't trust the revision date)
        approvals = sorted(
            approvals, key=lambda x: (x.id, x.lodgement_sequence), reverse=True
        )
        serializer = ApprovalHistorySerializer(approvals, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def action_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.action_logs.all()
        serializer = ApprovalUserActionSerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.comms_logs.all()
        serializer = ApprovalLogEntrySerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            mutable = request.data._mutable
            request.data._mutable = True
            request.data["approval"] = f"{instance.id}"
            request.data["staff"] = f"{request.user.id}"
            request.data._mutable = mutable
            serializer = ApprovalLogEntrySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comms = serializer.save()

            # Save the files
            for f in request.FILES.getlist("files"):
                document = comms.documents.create()
                document.name = str(f)
                document._file = f
                document.save()

            return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def invoices(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.invoices.all()
        serializer = InvoiceSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=["GET"],
        detail=True,
        renderer_classes=[DatatablesRenderer],
        pagination_class=DatatablesPageNumberPagination,
    )
    def related_items(self, request, *args, **kwargs):
        """Uses union to combine a queryset of multiple different model types
        and uses a generic related item serializer to return the data
        Note: Pagination is not working."""
        instance = self.get_object()
        proposals_queryset = (
            Proposal.objects.filter(
                approval__lodgement_number=instance.lodgement_number
            )
            .annotate(
                description=F("processing_status"),
                type=Value("proposal", output_field=CharField()),
            )
            .values("id", "lodgement_number", "description", "type")
        )
        compliances_queryset = instance.compliances.annotate(
            description=F("processing_status"),
            type=Value("compliance", output_field=CharField()),
        ).values("id", "lodgement_number", "processing_status", "type")
        queryset = proposals_queryset.union(compliances_queryset).order_by(
            "lodgement_number"
        )

        serializer = RelatedItemSerializer(queryset, many=True)
        data = {}
        # Add the fields that the datatables renderer expects
        data["data"] = serializer.data
        data["recordsFiltered"] = queryset.count()
        data["recordsTotal"] = queryset.count()
        return Response(data=data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def transfer(self, request, *args, **kwargs):
        logger.debug(f"Transfer request: {request.data}")
        instance = self.get_object()
        logger.debug(f"Approval: {instance}")
        active_transfers = ApprovalTransfer.objects.filter(
            approval=instance,
            processing_status__in=[
                ApprovalTransfer.APPROVAL_TRANSFER_STATUS_DRAFT,
                ApprovalTransfer.APPROVAL_TRANSFER_STATUS_PENDING,
            ],
        )
        if active_transfers.exists():
            logger.debug("Found active transfer")
            approval_transfer = active_transfers.first()
        else:
            logger.debug("Creating new transfer")
            approval_transfer = ApprovalTransfer.objects.create(
                approval=instance,
            )
            logger.info(
                f"Created Approval Transfer: {approval_transfer} for Approval: {instance}"
            )
            if instance.current_proposal.ind_applicant:
                ApprovalTransferApplicant.instantiate_from_request_user(
                    request.user, approval_transfer
                )

        serializer = ApprovalTransferSerializer(approval_transfer)
        return Response(serializer.data)


class CheckRefereeEmailThrottle(UserRateThrottle):
    if settings.DEBUG:
        rate = "2000/day"
    else:
        rate = "4/hour"


class ApprovalTransferViewSet(LicensingViewSet):
    queryset = ApprovalTransfer.objects.all()
    serializer_class = ApprovalTransferSerializer
    permission_classes = [IsAssessor | HasObjectPermission]

    def get_queryset(self):
        if is_internal(self.request):
            return ApprovalTransfer.objects.all()
        elif is_customer(self.request):
            user_orgs = get_organisation_ids_for_user(self.request.user.id)
            queryset = ApprovalTransfer.objects.filter(
                Q(approval__current_proposal__org_applicant_id__in=user_orgs)
                | Q(approval__current_proposal__submitter=self.request.user.id)
                | Q(
                    transferee_type=ApprovalTransfer.TRANSFEREE_TYPE_ORGANISATION,
                    transferee__in=user_orgs,
                )
                | Q(
                    transferee_type=ApprovalTransfer.TRANSFEREE_TYPE_INDIVIDUAL,
                    transferee=self.request.user.id,
                )
            )
            logger.debug(queryset.query)
            return queryset
        return ApprovalTransfer.objects.none()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_supporting_document(self, request, *args, **kwargs):
        logger.debug(f"{kwargs}")
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="approval_transfer_supporting_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    @basic_exception_handler
    def initiate(self, request, *args, **kwargs):
        self.update(request, *args, **kwargs)
        instance = self.get_object()
        instance.initiate(request.user.id)
        serializer = ApprovalTransferSerializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    @basic_exception_handler
    def cancel(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.cancel(request.user)
        serializer = ApprovalTransferSerializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
        throttle_classes=[CheckRefereeEmailThrottle],
    )
    @basic_exception_handler
    def check_transferee_email(self, request, *args, **kwargs):
        self.get_object()
        logger.debug(request.data)
        transferee_email = request.data.get("transferee_email", None)
        if not transferee_email:
            raise serializers.ValidationError("transferee_email not provided")
        try:
            emailuser = EmailUser.objects.get(email=transferee_email)
        except EmailUser.DoesNotExist:
            return Response({"email": transferee_email, "exists": False})

        return Response(
            {
                "transferee": emailuser.id,
                "transferee_name": emailuser.get_full_name(),
                "email": transferee_email,
                "exists": True,
            }
        )
