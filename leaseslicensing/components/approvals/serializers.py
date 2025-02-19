import logging

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from leaseslicensing.components.approvals.models import (
    Approval,
    ApprovalDocument,
    ApprovalLogEntry,
    ApprovalTransfer,
    ApprovalTransferApplicant,
    ApprovalType,
    ApprovalUserAction,
)
from leaseslicensing.components.competitive_processes.utils import (
    get_competitive_process_geometries_for_map_component,
)
from leaseslicensing.components.invoicing.serializers import InvoicingDetailsSerializer
from leaseslicensing.components.main.serializers import (
    CommunicationLogEntrySerializer,
    EmailUserSerializer,
)
from leaseslicensing.components.main.utils import get_secure_file_url
from leaseslicensing.components.organisations.models import Organisation
from leaseslicensing.components.organisations.serializers import OrganisationSerializer
from leaseslicensing.components.proposals.models import ProposalApplicant
from leaseslicensing.components.proposals.serializers import (
    ProposalGisDataSerializer,
    ProposalSerializer,
)
from leaseslicensing.components.proposals.utils import (
    get_proposal_geometries_for_map_component,
)
from leaseslicensing.components.users.serializers import UserSerializer
from leaseslicensing.helpers import is_approver, is_assessor, is_finance_officer

logger = logging.getLogger(__name__)


class ApprovalPaymentSerializer(serializers.ModelSerializer):
    # proposal = serializers.SerializerMethodField(read_only=True)
    org_applicant = serializers.SerializerMethodField(read_only=True)
    other_allowed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Approval
        fields = (
            "lodgement_number",
            "current_proposal",
            "expiry_date",
            "org_applicant",
            "other_allowed",
        )
        read_only_fields = (
            "lodgement_number",
            "current_proposal",
            "expiry_date",
            "org_applicant",
            "other_allowed",
        )

    def get_org_applicant(self, obj):
        return (
            obj.current_proposal.org_applicant.name
            if obj.current_proposal and obj.current_proposal.org_applicant
            else None
        )

    def get_other_allowed(self, obj):
        return settings.OTHER_PAYMENT_ALLOWED


class ApprovalTransferApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalTransferApplicant
        fields = "__all__"


class ApprovalTransferApplicantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalTransferApplicant
        exclude = ("approval_transfer",)

    def validate(self, attrs):
        errors = []

        required_fields = [
            "first_name",
            "last_name",
            "residential_line1",
            "residential_locality",
            "residential_state",
            "residential_country",
            "residential_postcode",
            "postal_line1",
            "postal_locality",
            "postal_state",
            "postal_country",
            "postal_postcode",
            "email",
            "phone_number",
            "mobile_number",
        ]

        for field in required_fields:
            if not attrs.get(field):
                errors.append(_(f"{field.replace('_', ' ').title()} is required"))

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)


class ApprovalTransferSerializer(serializers.ModelSerializer):
    transferee_name = serializers.CharField(read_only=True)
    applicant = ApprovalTransferApplicantSerializer(read_only=True, allow_null=True)
    applicant_for_writing = ApprovalTransferApplicantUpdateSerializer(
        write_only=True, allow_null=True
    )
    has_supporting_documents = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApprovalTransfer
        fields = "__all__"

    def validate(self, attrs):
        errors = []

        if not attrs.get("transferee"):
            errors.append(_("Please select a transferee"))

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)

    def update(self, instance, validated_data):
        logger.debug(validated_data)
        applicant_for_writing = validated_data.get("applicant_for_writing", None)
        if applicant_for_writing:
            applicant_data = validated_data.pop("applicant_for_writing")
            if hasattr(instance, "applicant"):
                serializer = ApprovalTransferApplicantUpdateSerializer(
                    instance.applicant, data=applicant_data
                )
            else:
                serializer = ApprovalTransferApplicantUpdateSerializer(
                    data=applicant_data
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return super().update(instance, validated_data)


class ApprovalSerializer(serializers.ModelSerializer):
    applicant_type = serializers.SerializerMethodField(read_only=True)
    applicant_id = serializers.SerializerMethodField(read_only=True)
    licence_document = serializers.SerializerMethodField()
    renewal_document = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source="get_status_display")
    application_type = serializers.SerializerMethodField(read_only=True)
    linked_applications = serializers.SerializerMethodField(read_only=True)
    can_renew = serializers.SerializerMethodField()
    can_initiate_transfer = serializers.BooleanField(read_only=True)
    has_pending_transfer = serializers.BooleanField(read_only=True)
    has_draft_transfer = serializers.BooleanField(read_only=True)
    active_transfer = ApprovalTransferSerializer(read_only=True, allow_null=True)
    is_assessor = serializers.SerializerMethodField()
    is_approver = serializers.SerializerMethodField()
    is_finance_officer = serializers.SerializerMethodField()
    requirement_docs = serializers.SerializerMethodField()
    submitter = serializers.SerializerMethodField()
    holder = serializers.SerializerMethodField()
    holder_obj = serializers.SerializerMethodField()
    groups_comma_list = serializers.SerializerMethodField(read_only=True)
    site_name = serializers.CharField(
        source="current_proposal.site_name.name", allow_null=True, read_only=True
    )
    groups_names_list = serializers.ListField(
        source="current_proposal.groups_names_list", read_only=True
    )
    categories_list = serializers.ListField(
        source="current_proposal.categories_list", read_only=True
    )
    invoicing_details = InvoicingDetailsSerializer(
        source="current_proposal.invoicing_details", read_only=True
    )
    current_proposal_processing_status = serializers.CharField(
        source="current_proposal.processing_status", read_only=True
    )
    current_proposal_proposal_type = serializers.CharField(
        source="current_proposal.proposal_type", read_only=True
    )
    current_proposal_proposal_type_code = serializers.CharField(
        source="current_proposal.proposal_type.code", read_only=True
    )
    approval_type = serializers.CharField(
        source="approval_type.name", allow_null=True, read_only=True
    )
    approval_type__type = serializers.SerializerMethodField(read_only=True)
    gis_data = serializers.SerializerMethodField(read_only=True)
    geometry_objs = serializers.SerializerMethodField(read_only=True)
    approved_by = serializers.SerializerMethodField()
    renewed_from_id = serializers.IntegerField(allow_null=True, read_only=True)
    renewed_from = serializers.CharField(allow_null=True, read_only=True)
    current_proposal = ProposalSerializer(read_only=True)

    class Meta:
        model = Approval
        fields = (
            "id",
            "lodgement_number",
            "linked_applications",
            "licence_document",
            "renewal_document",
            "current_proposal",
            "current_proposal_processing_status",
            "current_proposal_proposal_type",
            "current_proposal_proposal_type_code",
            "tenure",
            "renewal_notification_sent_to_holder",
            "issue_date",
            "original_issue_date",
            "start_date",
            "expiry_date",
            "surrender_details",
            "suspension_details",
            "applicant_type",
            "applicant_id",
            "holder",
            "holder_obj",
            "extracted_fields",
            "status",
            "reference",
            "can_reissue",
            "cancellation_date",
            "cancellation_details",
            "can_action",
            "set_to_cancel",
            "set_to_surrender",
            "set_to_suspend",
            "can_renew",
            "can_amend",
            "can_reinstate",
            "can_initiate_transfer",
            "has_pending_transfer",
            "has_draft_transfer",
            "active_transfer",
            "has_pending_renewal",
            "has_draft_renewal",
            "active_renewal",
            "has_draft_amendment",
            "active_amendment",
            "application_type",
            "original_leaselicence_number",
            "migrated",
            "is_assessor",
            "is_approver",
            "is_finance_officer",
            "requirement_docs",
            "submitter",
            "groups_comma_list",
            "groups_names_list",
            "categories_list",
            "site_name",
            "record_management_number",
            "invoicing_details",
            "approval_type",
            "approval_type__type",
            "gis_data",
            "geometry_objs",
            "approved_by",
            "renewed_from_id",
            "renewed_from",
        )
        # the serverSide functionality of datatables is such that only columns that have
        # field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            "id",
            "status",
            "reference",
            "lodgement_number",
            "linked_applications",
            "licence_document",
            "start_date",
            "expiry_date",
            "holder",
            "holder_obj",
            "can_reissue",
            "can_action",
            "can_reinstate",
            "can_amend",
            "can_renew",
            "can_initiate_transfer",
            "has_pending_transfer",
            "has_draft_transfer",
            "has_pending_renewal",
            "has_draft_renewal",
            "active_renewal",
            "has_draft_amendment",
            "active_amendment",
            "set_to_cancel",
            "set_to_suspend",
            "set_to_surrender",
            "current_proposal",  # current proposal id is (at least) needed for renewal
            "current_proposal_processing_status",
            "renewal_notification_sent_to_holder",
            "application_type",
            "migrated",
            "is_assessor",
            "is_approver",
            "is_finance_officer",
            "requirement_docs",
            "submitter",
            "groups_comma_list",
            "invoicing_details",
            "renewed_from_id",
            "renewed_from",
        )

    def get_licence_document(self, obj):
        if not obj.licence_document or not obj.licence_document._file:
            return None
        return get_secure_file_url(obj.licence_document, "_file")

    def get_submitter(self, obj):
        if not obj.submitter:
            return None
        user = EmailUser.objects.get(id=obj.submitter)
        return EmailUserSerializer(user).data

    def get_linked_applications(self, obj):
        return obj.linked_applications

    def get_renewal_document(self, obj):
        if not obj.renewal_document or not obj.renewal_document._file:
            return None
        return obj.renewal_document._file.url

    def get_application_type(self, obj):
        if obj.current_proposal:
            if obj.current_proposal.application_type:
                return obj.current_proposal.application_type.name_display
        return None

    def get_holder(self, obj):
        return obj.holder

    def get_applicant_type(self, obj):
        if isinstance(obj.applicant, Organisation):
            return "organisation"
        elif isinstance(obj.applicant, ProposalApplicant):
            return "individual"
        elif isinstance(obj.applicant, EmailUser):
            return "individual"
        else:
            return "Applicant not yet assigned"

    def get_applicant_id(self, obj):
        return obj.applicant_id

    def get_holder_obj(self, obj):
        if isinstance(obj.applicant, Organisation):
            return OrganisationSerializer(obj.applicant).data
        return UserSerializer(obj.applicant).data

    def get_can_renew(self, obj):
        if not obj.can_renew:
            return False
        request = self.context["request"]
        if is_assessor(request):
            return obj.status == obj.APPROVAL_STATUS_CURRENT_PENDING_RENEWAL_REVIEW
        return obj.status == obj.APPROVAL_STATUS_CURRENT_PENDING_RENEWAL

    def get_is_assessor(self, obj):
        request = self.context["request"]
        return is_assessor(request)

    def get_is_approver(self, obj):
        request = self.context["request"]
        return is_approver(request)

    def get_is_finance_officer(self, obj):
        request = self.context["request"]
        return is_finance_officer(request)

    def get_requirement_docs(self, obj):
        if obj.requirement_docs and obj.requirement_docs._file:
            return [[d.name, d._file.url] for d in obj.requirement_docs]
        return None

    def get_groups_comma_list(self, obj):
        return obj.current_proposal.groups_comma_list

    def get_gis_data(self, obj):
        return ProposalGisDataSerializer(obj.current_proposal).data

    def get_geometry_objs(self, obj):
        """
        Returns proposal and competitive process geometry objects for this license
        """

        geometry_data = {"type": "FeatureCollection", "features": []}
        geometry_data = get_proposal_geometries_for_map_component(
            obj.current_proposal, self.context, geometry_data
        )
        geometry_data = get_competitive_process_geometries_for_map_component(
            obj.current_proposal.originating_competitive_process,
            self.context,
            geometry_data,
        )

        return geometry_data

    def get_approved_by(self, obj):
        proposed_issuance_approval = (
            obj.current_proposal.proposed_issuance_approval or {}
        )
        approved_by_id = proposed_issuance_approval.get("approved_by", None)
        if not approved_by_id:
            return "Approver not assigned"
        user = EmailUser.objects.get(id=approved_by_id)
        return user.get_full_name()

    def get_approval_type__type(self, obj):
        if obj.approval_type.type is None:
            return None  # Check for no type because type property is nullable
        return obj.approval_type.type.title()


class ApprovalKeyValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = ("id", "lodgement_number")


class ApprovalExtendSerializer(serializers.Serializer):
    extend_details = serializers.CharField()


class ApprovalCancellationSerializer(serializers.Serializer):
    cancellation_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    cancellation_details = serializers.CharField()


class ApprovalSuspensionSerializer(serializers.Serializer):
    from_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    to_date = serializers.DateField(
        input_formats=["%d/%m/%Y"], required=False, allow_null=True
    )
    suspension_details = serializers.CharField()


class ApprovalSurrenderSerializer(serializers.Serializer):
    surrender_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    surrender_details = serializers.CharField()


class ApprovalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source="who_full_name")

    class Meta:
        model = ApprovalUserAction
        fields = "__all__"


class ApprovalLogEntrySerializer(CommunicationLogEntrySerializer):
    class Meta:
        model = ApprovalLogEntry
        fields = "__all__"
        read_only_fields = ("customer",)


class ApprovalDocumentHistorySerializer(serializers.ModelSerializer):
    history_date = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    filename = serializers.CharField()
    reason = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = ApprovalDocument
        fields = (
            "id",
            "history_date",
            "url",
            "filename",
            "reason",
        )

    def get_history_date(self, obj):
        date_format_loc = timezone.localtime(obj.uploaded_date)
        history_date = date_format_loc.strftime("%d/%m/%Y %H:%M:%S.%f")

        return history_date

    def get_url(self, obj):
        revision_id = self.context.get("revision_id", None)
        if not obj or not obj._file:
            return None
        return get_secure_file_url(obj, "_file", revision_id=revision_id)

    def get_filename(self, obj):
        if not obj or not obj._file:
            return None
        return obj.filename


class ApprovalHistorySerializer(serializers.ModelSerializer):
    revision_id = serializers.SerializerMethodField()
    lodgement_number = serializers.SerializerMethodField()
    licence_document = serializers.SerializerMethodField()
    sign_off_sheet = serializers.SerializerMethodField()
    cover_letter = serializers.SerializerMethodField()
    application = serializers.SerializerMethodField()
    approval_type = serializers.SerializerMethodField()
    holder = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    start_date_str = serializers.SerializerMethodField()
    expiry_date_str = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()
    application_detail_url = serializers.SerializerMethodField()
    version_date_str = serializers.DateTimeField(source="version_date", format="%d/%m/%Y %H:%M:%S")
    revision_comment = serializers.CharField()

    class Meta:
        model = Approval
        fields = (
            "id",
            "revision_id",
            "lodgement_number",
            "licence_document",
            "sign_off_sheet",
            "cover_letter",
            "application",
            "approval_type",
            "holder",
            "status",
            "start_date_str",
            "expiry_date_str",
            "reason",
            "application_detail_url",
            "version_date_str",
            "revision_comment",
        )

    def get_revision_id(self, obj):
        return obj.revision_id

    def get_lodgement_number(self, obj):
        return f"{obj.lodgement_number}-{obj.lodgement_sequence}"

    def get_licence_document(self, obj):
        try:
            document = obj.licence_document
        except ApprovalDocument.DoesNotExist:
            return None
        else:
            if not document or not document._file:
                return None
            return ApprovalDocumentHistorySerializer(
                document, context={"revision_id": obj.revision_id}
            ).data

    def get_sign_off_sheet(self, obj):
        try:
            document = obj.sign_off_sheet
        except ApprovalDocument.DoesNotExist:
            return None
        else:
            if not document or not document._file:
                return None
            return ApprovalDocumentHistorySerializer(
                document, context={"revision_id": obj.revision_id}
            ).data

    def get_cover_letter(self, obj):
        try:
            document = obj.cover_letter_document
        except ApprovalDocument.DoesNotExist:
            return None
        else:
            if not document or not document._file:
                return None
            return ApprovalDocumentHistorySerializer(
                document, context={"revision_id": obj.revision_id}
            ).data

    def get_application(self, obj):
        return obj.current_proposal.lodgement_number

    def get_approval_type(self, obj):
        return ApprovalTypeSerializer(obj.approval_type).data

    def get_holder(self, obj):
        return obj.holder

    def get_status(self, obj):
        return obj.get_status_display()

    def get_start_date_str(self, obj):
        return obj.start_date.strftime("%d/%m/%Y")

    def get_expiry_date_str(self, obj):
        return obj.expiry_date.strftime("%d/%m/%Y")

    def get_reason(self, obj):
        if obj.status == Approval.APPROVAL_STATUS_CURRENT:
            # For current licenses return the reason of the last change to the approval document
            return (
                obj.licence_document.get_reason_display()
                if obj.licence_document
                else ""
            )
        # Else (Cancel, Surrender, Suspend) return the status of the approval
        return obj.get_status_display()

    def get_application_detail_url(self, obj):
        return reverse(
            "internal-proposal-detail", kwargs={"pk": obj.current_proposal.id}
        )


class ApprovalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalType
        fields = "__all__"


class ApprovalBasicSerializer(serializers.ModelSerializer):
    approval_type = serializers.CharField(source="approval_type.type", read_only=True)
    approval_type_name = serializers.CharField(
        source="approval_type.name", read_only=True
    )
    active_transfer = ApprovalTransferSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Approval
        fields = (
            "id",
            "lodgement_number",
            "start_date",
            "expiry_date",
            "issue_date",
            "approval_type",
            "approval_type_name",
            "holder",
            "has_outstanding_compliances",
            "has_outstanding_invoices",
            "has_missing_gross_turnover_entries",
            "holder",
            "active_transfer",
        )
