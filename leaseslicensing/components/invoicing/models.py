import logging
from datetime import datetime
from decimal import Decimal

import pytz
from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import F, Sum, Window
from django.db.models.functions import Coalesce
from ledger_api_client import settings_base

from leaseslicensing.components.main.models import (
    LicensingModel,
    RevisionedMixin,
    SecureFileField,
)

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    modified_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True


class ChargeMethod(models.Model):
    key = models.CharField(max_length=200, unique=True)
    display_name = models.CharField(
        max_length=200,
    )
    display_order = models.IntegerField(default=0)

    class Meta:
        app_label = "leaseslicensing"
        ordering = ["display_order"]

    def __str__(self):
        return self.display_name


class RepetitionType(models.Model):
    key = models.CharField(max_length=200, unique=True)
    display_name = models.CharField(
        max_length=200,
    )

    class Meta:
        app_label = "leaseslicensing"

    def __str__(self):
        return self.display_name


class ReviewDateAnnually(BaseModel):
    review_date = models.DateField(null=True, blank=True)
    date_of_enforcement = models.DateField()

    class Meta:
        app_label = "leaseslicensing"
        verbose_name_plural = "Review Date Annually"

    @staticmethod
    def get_review_date_annually_by_date(
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
    ):
        """
        Return an setting object which is enabled at the target_date
        """
        review_date_annually = (
            ReviewDateAnnually.objects.filter(
                date_of_enforcement__lte=target_date,
            )
            .order_by("date_of_enforcement")
            .last()
        )
        return review_date_annually


class ReviewDateQuarterly(BaseModel):
    review_date_q1 = models.DateField()
    review_date_q2 = models.DateField()
    review_date_q3 = models.DateField()
    review_date_q4 = models.DateField()
    date_of_enforcement = models.DateField()

    class Meta:
        app_label = "leaseslicensing"
        verbose_name_plural = "Review Date Quarterly"

    @staticmethod
    def get_review_date_quarterly_by_date(
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
    ):
        """
        Return an setting object which is enabled at the target_date
        """
        review_date_quarterly = (
            ReviewDateQuarterly.objects.filter(
                date_of_enforcement__lte=target_date,
            )
            .order_by("date_of_enforcement")
            .last()
        )
        return review_date_quarterly


class ReviewDateMonthly(BaseModel):
    review_date = models.PositiveSmallIntegerField(null=True, blank=True)
    date_of_enforcement = models.DateField()

    class Meta:
        app_label = "leaseslicensing"
        verbose_name_plural = "Review Date Monthly"

    @staticmethod
    def get_review_date_monthly_by_date(
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
    ):
        """
        Return an setting object which is enabled at the target_date
        """
        review_date_monthly = (
            ReviewDateMonthly.objects.filter(
                date_of_enforcement__lte=target_date,
            )
            .order_by("date_of_enforcement")
            .last()
        )
        return review_date_monthly


class InvoicingDateAnnually(BaseModel):
    invoicing_date = models.DateField(null=True, blank=True)
    date_of_enforcement = models.DateField()

    class Meta:
        app_label = "leaseslicensing"
        verbose_name_plural = "Invoicing Date Annually"

    @staticmethod
    def get_invoicing_date_annually_by_date(
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
    ):
        """
        Return an setting object which is enabled at the target_date
        """
        invoicing_date_annually = (
            InvoicingDateAnnually.objects.filter(
                date_of_enforcement__lte=target_date,
            )
            .order_by("date_of_enforcement")
            .last()
        )
        return invoicing_date_annually


class InvoicingDateQuarterly(BaseModel):
    invoicing_date_q1 = models.DateField()
    invoicing_date_q2 = models.DateField()
    invoicing_date_q3 = models.DateField()
    invoicing_date_q4 = models.DateField()
    date_of_enforcement = models.DateField()

    class Meta:
        app_label = "leaseslicensing"
        verbose_name_plural = "Invoicing Date Quarterly"

    @staticmethod
    def get_invoicing_date_quarterly_by_date(
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
    ):
        """
        Return an setting object which is enabled at the target_date
        """
        invoicing_date_quarterly = (
            InvoicingDateQuarterly.objects.filter(
                date_of_enforcement__lte=target_date,
            )
            .order_by("date_of_enforcement")
            .last()
        )
        return invoicing_date_quarterly


class InvoicingDateMonthly(BaseModel):
    invoicing_date = models.PositiveSmallIntegerField(null=True, blank=True)
    date_of_enforcement = models.DateField()

    class Meta:
        app_label = "leaseslicensing"
        verbose_name_plural = "Invoicing Date Monthly"

    @staticmethod
    def get_invoicing_date_monthly_by_date(
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
    ):
        """
        Return an setting object which is enabled at the target_date
        """
        invoicing_date_monthly = (
            InvoicingDateMonthly.objects.filter(
                date_of_enforcement__lte=target_date,
            )
            .order_by("date_of_enforcement")
            .last()
        )
        return invoicing_date_monthly


def get_year():
    cpis = ConsumerPriceIndex.objects.all()
    if cpis:
        latest_cpis = cpis.order_by("year").last()
        return getattr(latest_cpis, "year") + 1
    else:
        return ConsumerPriceIndex.start_year


class ConsumerPriceIndex(BaseModel):
    start_year = 2021

    time_period = models.CharField(max_length=7, help_text="Year and Quarter")
    value = models.FloatField(
        help_text="Percentage Change from Corresponding Quarter of the Previous Year"
    )

    class Meta:
        app_label = "leaseslicensing"
        verbose_name = "CPI Data"
        verbose_name_plural = "CPI Data"

    def __str__(self):
        return f"{self.time_period}: {self.value}"


class InvoicingDetailsManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "annual_increment_amounts",
                "annual_increment_percentages",
                "gross_turnover_percentages",
                "crown_land_rent_review_dates",
            )
        )


class InvoicingDetails(BaseModel):
    """
    This is the main model to store invoicing details, generated by a proposal first
    (Proposal has a field: invoicing_details)
    then copied and/or edited as business run
    """

    objects = InvoicingDetailsManager()

    charge_method = models.ForeignKey(
        ChargeMethod, null=True, blank=True, on_delete=models.SET_NULL
    )
    base_fee_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    once_off_charge_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    review_once_every = models.PositiveSmallIntegerField(
        null=True, blank=True, default=1
    )
    review_repetition_type = models.ForeignKey(
        RepetitionType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoicing_details_set_for_review",
    )
    invoicing_once_every = models.PositiveSmallIntegerField(
        null=True, blank=True, default=1
    )  # Probably better to call this times per repetition?
    invoicing_repetition_type = models.ForeignKey(
        RepetitionType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoicing_details_set_for_invoicing",
    )
    approval = models.ForeignKey(
        "Approval",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoicing_details",
    )
    previous_invoicing_details = models.OneToOneField(
        "self",
        null=True,
        blank=True,
        related_name="next_invoicing_details",
        on_delete=models.SET_NULL,
    )

    class Meta:
        app_label = "leaseslicensing"

        # constraints = [
        #     models.CheckConstraint(
        #         check=Q(base_fee_amount=0) | Q(once_off_charge_amount=0),
        #         name='either_one_null',
        #     )
        # ]

    def calculate_amount(
        self,
        target_date=datetime.now(pytz.timezone(settings_base.TIME_ZONE)).date(),
        span=relativedelta(years=1),
    ):
        pass
        # TODO: Calculate invoice amount
        # 1. Check if it has been already created
        #   OR
        # 1. Calculate the last date which is covered by the invoices
        # CHARGE_METHOD_ONCE_OFF_CHARGE
        # CHARGE_METHOD_BASE_FEE_PLUS_FIXED_ANNUAL_INCREMENT
        # CHARGE_METHOD_BASE_FEE_PLUS_FIXED_ANNUAL_PERCENTAGE
        # CHARGE_METHOD_BASE_FEE_PLUS_ANNUAL_CPI
        # CHARGE_METHOD_PERCENTAGE_OF_GROSS_TURNOVER
        # CHARGE_METHOD_NO_RENT_OR_LICENCE_CHARGE


class FixedAnnualIncrementAmount(BaseModel):
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    increment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default="0.00", null=True, blank=True
    )
    invoicing_details = models.ForeignKey(
        InvoicingDetails,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="annual_increment_amounts",
    )

    class Meta:
        app_label = "leaseslicensing"
        ordering = [
            "year",
        ]

    @property
    def readonly(self):
        # TODO: implement
        return False


class FixedAnnualIncrementPercentage(BaseModel):
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    increment_percentage = models.FloatField(null=True, blank=True)
    invoicing_details = models.ForeignKey(
        InvoicingDetails,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="annual_increment_percentages",
    )

    class Meta:
        app_label = "leaseslicensing"
        ordering = [
            "year",
        ]

    @property
    def readonly(self):
        # TODO: implement
        return False


class PercentageOfGrossTurnover(BaseModel):
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    invoicing_details = models.ForeignKey(
        InvoicingDetails,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="gross_turnover_percentages",
    )

    class Meta:
        app_label = "leaseslicensing"
        ordering = [
            "year",
        ]

    @property
    def readonly(self):
        # TODO: implement
        return False


class CrownLandRentReviewDate(BaseModel):
    review_date = models.DateField(null=True, blank=True)
    invoicing_details = models.ForeignKey(
        InvoicingDetails,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="crown_land_rent_review_dates",
    )

    class Meta:
        app_label = "leaseslicensing"
        ordering = [
            "review_date",
        ]

    @property
    def readonly(self):
        # TODO: implement
        return False


class LeaseLicenceFee(BaseModel):
    """
    This model handles each invoice and the information surrounding it.
    An object of this model is created at an invoicing date.
    """

    invoicing_details = models.ForeignKey(
        InvoicingDetails,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lease_licence_fees",
    )
    invoice_reference = models.CharField(
        max_length=50, null=True, blank=True, default=""
    )
    invoice_cover_start_date = models.DateField(null=True, blank=True)
    invoice_cover_end_date = models.DateField(null=True, blank=True)
    date_invoice_sent = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "leaseslicensing"

    def __str__(self):
        if self.invoicing_details.approval:
            return f"Approval: {self.invoicing_details.approval}, Invoice: {self.invoice_reference}"
        else:
            return (
                f"Proposal: {self.invoicing_details}, Invoice: {self.invoice_reference}"
            )

    @property
    def invoice(self):
        invoice = None
        if self.invoice_reference:
            invoice = Invoice.objects.get(reference=self.invoice_reference)
        return invoice

    @property
    def amount(self):
        amount = None
        if self.invoice_reference:
            invoice = Invoice.objects.get(reference=self.invoice_reference)
            amount = invoice.amount
        return amount


def invoice_pdf_upload_path(instance, filename):
    return f"approvals/{instance.approval.id}/invoices/{instance.id}/{filename}"


class InvoiceManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("approval")
            .prefetch_related("transactions")
        )


class Invoice(LicensingModel):
    objects = InvoiceManager()

    MODEL_PREFIX = "I"

    INVOICE_STATUS_UNPAID = "unpaid"
    INVOICE_STATUS_PAID = "paid"
    INVOICE_STATUS_VOID = "void"
    INVOICE_STATUS_CHOICES = (
        (INVOICE_STATUS_UNPAID, "Unpaid"),
        (INVOICE_STATUS_PAID, "Paid"),
        (INVOICE_STATUS_VOID, "Void"),
    )
    approval = models.ForeignKey(
        "Approval",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    status = models.CharField(
        max_length=40, choices=INVOICE_STATUS_CHOICES, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    inc_gst = models.BooleanField(default=True)
    date_issued = models.DateTimeField(auto_now_add=True, null=False)
    date_updated = models.DateTimeField(auto_now=True, null=False)
    date_due = models.DateField(null=True, blank=False)

    # Not sure if we will need this, the invoice file may exist within ledger
    invoice_pdf = SecureFileField(
        upload_to=invoice_pdf_upload_path, null=True, blank=True
    )
    oracle_invoice_number = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        app_label = "leaseslicensing"
        ordering = ["-date_issued", "approval"]

    def __str__(self):
        return (
            f"Invoice: {self.lodgement_number} for Approval: {self.approval} "
            f"of Amount: {self.amount} with Status: {self.status}"
        )

    def user_has_object_permission(self, user_id):
        self.approval.user_has_object_permission(user_id)

    @property
    def balance(self):
        credit_debit_sums = self.transactions.aggregate(
            credit=Coalesce(models.Sum("credit"), Decimal("0.00")),
            debit=Coalesce(models.Sum("debit"), Decimal("0.00")),
        )
        balance = self.amount + credit_debit_sums["credit"] - credit_debit_sums["debit"]
        logger.debug(f"Balance for Invoice: {self} is {balance}")
        return Decimal(balance).quantize(Decimal("0.01"))


class InvoiceTransactionManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                cumulative_balance=Window(
                    expression=Sum("debit"),
                    order_by=F("datetime_created").asc(),
                )
                - Window(
                    expression=Sum("credit"),
                    order_by=F("datetime_created").asc(),
                )
            )
        )


class InvoiceTransaction(RevisionedMixin, models.Model):
    objects = InvoiceTransactionManager()
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=False,
        blank=False,
    )
    credit = models.DecimalField(
        max_digits=9, decimal_places=2, blank=False, null=False, default=Decimal("0.00")
    )
    debit = models.DecimalField(
        max_digits=9, decimal_places=2, blank=False, null=False, default=Decimal("0.00")
    )
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "leaseslicensing"
        ordering = ["datetime_created"]

    def __str__(self):
        return f"Transaction: {self.id} for Invoice: {self.invoice} Credit: {self.credit}, Debit: {self.debit}"
