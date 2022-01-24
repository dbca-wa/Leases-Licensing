from django.conf import settings
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address
from leaseslicensing.components.main.models import ApplicationType
from leaseslicensing.components.organisations.models import Organisation
from leaseslicensing.components.proposals.models import (
                                    ProposalType,
                                    Proposal,
                                    ProposalUserAction,
                                    ProposalLogEntry,
                                    Referral,
                                    ProposalRequirement,
                                    ProposalStandardRequirement,
                                    ProposalDeclinedDetails,
                                    AmendmentRequest,
                                    AmendmentReason,
                                    ProposalApplicantDetails,
                                    QAOfficerReferral,
                                    ProposalOtherDetails,
                                    ChecklistQuestion,
                                    ProposalAssessmentAnswer,
                                    ProposalAssessment,
                                    RequirementDocument,
                                    ProposalGeometry,
                                )
from leaseslicensing.components.main.serializers import CommunicationLogEntrySerializer, ApplicationTypeSerializer
from leaseslicensing.components.organisations.serializers import OrganisationSerializer
from leaseslicensing.components.users.serializers import UserAddressSerializer, DocumentSerializer
from rest_framework import serializers
from django.db.models import Q
from leaseslicensing.ledger_api_utils import retrieve_email_user
from rest_framework_gis.serializers import GeoFeatureModelSerializer
#from reversion.models import Version

# still required
class ProposalGeometrySaveSerializer(GeoFeatureModelSerializer):
    proposal_id = serializers.IntegerField(write_only=True, required=False)
    class Meta:
        model = ProposalGeometry
        geo_field = 'polygon'
        fields = (
            'id',
            'proposal_id',
            'polygon',
            'intersects',
        )
        read_only_fields=('id',)


class ProposalGeometrySerializer(GeoFeatureModelSerializer):
    proposal_id = serializers.IntegerField(write_only=True, required=False)
    class Meta:
        model = ProposalGeometry
        geo_field = 'polygon'
        fields = (
            'id',
            'proposal_id',
            'polygon',
            'intersects',
        )
        read_only_fields=('id',)


class ProposalTypeSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()
    class Meta:
        model = ProposalType
        fields = (
            'id',
            'code',
            'description',
        )


    def get_activities(self,obj):
        return obj.activities.names()

class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = ('id','email','first_name','last_name','title','organisation')

class EmailUserAppViewSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    #identification = DocumentSerializer()

    class Meta:
        model = EmailUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'dob',
                  'title',
                  'organisation',
                  'residential_address',
                  #'identification',
                  'email',
                  'phone_number',
                  'mobile_number',)

class ProposalApplicantDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalApplicantDetails
        fields = ('id','first_name')


class QAOfficerReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.SerializerMethodField(read_only=True)
    sent_by = serializers.SerializerMethodField(read_only=True)
    qaofficer = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = QAOfficerReferral
        fields = '__all__'

    def get_processing_status(self,obj):
        return obj.get_processing_status_display()

    def get_sent_by(self,obj):
        return obj.sent_by.get_full_name() if obj.sent_by else ''

    def get_qaofficer(self,obj):
        return obj.qaofficer.get_full_name() if obj.qaofficer else ''

class ProposalOtherDetailsSerializer(serializers.ModelSerializer):
    #park=ParkSerializer()
    #accreditation_type= serializers.SerializerMethodField()
    #accreditation_expiry = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    nominated_start_date = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    insurance_expiry = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    preferred_licence_period = serializers.CharField(allow_blank=True, allow_null=True)
    proposed_end_date = serializers.DateField(format="%d/%m/%Y",read_only=True)

    class Meta:
        model = ProposalOtherDetails
        #fields = '__all__'
        fields=(
                #'accreditation_type',
                #'accreditation_expiry',
                'id',
                'preferred_licence_period',
                'nominated_start_date',
                'insurance_expiry',
                'other_comments',
                'credit_fees',
                'credit_docket_books',
                'docket_books_number',
                'mooring',
                'proposed_end_date',
                )


class SaveProposalOtherDetailsSerializer(serializers.ModelSerializer):
    #park=ParkSerializer()
    class Meta:
        model = ProposalOtherDetails
        #fields = '__all__'
        fields=(
                # 'accreditation_type',
                # 'accreditation_expiry',
                'preferred_licence_period',
                'nominated_start_date',
                'insurance_expiry',
                'other_comments',
                'credit_fees',
                'credit_docket_books',
                'proposal',
                )


class ChecklistQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistQuestion
        #fields = '__all__'
        fields=('id',
                'text',
                'answer_type',
                )
class ProposalAssessmentAnswerSerializer(serializers.ModelSerializer):
    question=ChecklistQuestionSerializer(read_only=True)
    class Meta:
        model = ProposalAssessmentAnswer
        fields = ('id',
                'question',
                'answer',
                'text_answer',
                )

class ProposalAssessmentSerializer(serializers.ModelSerializer):
    #checklist=ProposalAssessmentAnswerSerializer(many=True, read_only=True)
    checklist=serializers.SerializerMethodField()

    class Meta:
        model = ProposalAssessment
        fields = ('id',
                'completed',
                'submitter',
                'referral_assessment',
                'referral_group',
                'referral_group_name',
                'checklist'
                )

    def get_checklist(self,obj):
        qs= obj.checklist.order_by('question__order')
        return ProposalAssessmentAnswerSerializer(qs, many=True, read_only=True).data


class BaseProposalSerializer(serializers.ModelSerializer):
    readonly = serializers.SerializerMethodField(read_only=True)
    documents_url = serializers.SerializerMethodField()
    proposal_type = serializers.SerializerMethodField()
    application_type = ApplicationTypeSerializer()
    allowed_assessors = EmailUserSerializer(many=True)
    qaofficer_referrals = QAOfficerReferralSerializer(many=True)

    #get_history = serializers.ReadOnlyField()
    is_qa_officer = serializers.SerializerMethodField()
    # application_type_display = serializers.SerializerMethodField()
    #fee_invoice_url = serializers.SerializerMethodField()
    #proposalgeometry = ProposalGeometrySerializer()
    proposalgeometry = ProposalGeometrySerializer(many=True, read_only=True)

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                # 'application_type_display',
                'proposal_type',
                'approval_level',
                'title',
                'customer_status',
                'processing_status',
                'review_status',
                'applicant_type',
                'applicant',
                'org_applicant',
                'proxy_applicant',
                'submitter',
                'assigned_officer',
                'previous_application',
                'get_history',
                'lodgement_date',
                #'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'allowed_assessors',
                'proposal_type',
                'is_qa_officer',
                'qaofficer_referrals',
                'pending_amendment_request',
                'is_amendment_proposal',

                # tab field models
                'applicant_details',
                #'fee_invoice_url',
                #'fee_paid',
                'details_text',
                'proposalgeometry',
                ## additional form fields
                'exclusive_use',
                'long_term_use',
                'consistent_purpose',
                'consistent_plan',
                'clearing_vegetation',
                'ground_disturbing_works',
                'heritage_site',
                'environmentally_sensitive',
                'wetlands_impact',
                'building_required',
                'significant_change',
                'aboriginal_site',
                'native_title_consultation',
                'mining_tenement',

                )
        read_only_fields=('documents',)

    def get_documents_url(self,obj):
        return '/media/{}/proposals/{}/documents/'.format(settings.MEDIA_APP_DIR, obj.id)

    def get_readonly(self,obj):
        return False

    # def get_application_type_display(self,obj):
    #     return obj.application_type.get_name_display()
    # def get_application_type(self, obj):
    #     return obj.get_application_type_display()

    def get_processing_status(self,obj):
        return obj.get_processing_status_display()

    def get_review_status(self,obj):
        return obj.get_review_status_display()

    def get_customer_status(self,obj):
        return obj.get_customer_status_display()

    def get_proposal_type(self,obj):
        return obj.proposal_type.description if obj.proposal_type else ''

    def get_is_qa_officer(self,obj):
        #request = self.context['request']
        #return request.user.email in obj.qa_officers()
        return True

    #def get_fee_invoice_url(self,obj):
     #   return '/cols/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None

    def get_allow_full_discount(self,obj):
        return True if obj.application_type.name==ApplicationType.TCLASS and obj.allow_full_discount else False


class ListProposalSerializer(BaseProposalSerializer):
    #submitter = EmailUserSerializer()
    submitter = serializers.SerializerMethodField(read_only=True)
    applicant = serializers.CharField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    assigned_officer = serializers.SerializerMethodField(read_only=True)

    # application_type = serializers.CharField(source='application_type.name', read_only=True)
    assessor_process = serializers.SerializerMethodField(read_only=True)
    qaofficer_referrals = QAOfficerReferralSerializer(many=True)
    #fee_invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'proposal_type',
                'approval_level',
                'title',
                'customer_status',
                'processing_status',
                'review_status',
                'applicant',
                'proxy_applicant',
                'submitter',
                'assigned_officer',
                'previous_application',
                'get_history',
                'lodgement_date',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'assessor_process',
                'allowed_assessors',
                'proposal_type',
                'qaofficer_referrals',
                'is_qa_officer',
                #'fee_invoice_url',
                #'fee_invoice_reference',
                #'fee_paid',
                )
        # the serverSide functionality of datatables is such that only columns that have field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
                'id',
                'application_type',
                'proposal_type',
                'title',
                'customer_status',
                'processing_status',
                'applicant',
                'submitter',
                'assigned_officer',
                'lodgement_date',
                'can_user_edit',
                'can_user_view',
                'reference',
                'lodgement_number',
                'can_officer_process',
                'assessor_process',
                'allowed_assessors',
                #'fee_invoice_url',
                #'fee_invoice_reference',
                #'fee_paid',
                )

    def get_submitter(self,obj):
        email_user = retrieve_email_user(obj.submitter)
        return EmailUserSerializer(email_user).data

    def get_assigned_officer(self,obj):
        if obj.processing_status==Proposal.PROCESSING_STATUS_WITH_APPROVER and obj.assigned_approver:
            return obj.assigned_approver.get_full_name()
        if obj.assigned_officer:
            return obj.assigned_officer.get_full_name()
        return None

    def get_assessor_process(self,obj):
        # Check if currently logged in user has access to process the proposal
        request = self.context['request']
        user = request.user
        if obj.can_officer_process:
            '''if (obj.assigned_officer and obj.assigned_officer == user) or (user in obj.allowed_assessors):
                return True'''
            if obj.assigned_officer:
                if obj.assigned_officer == user:
                    return True
            elif user in obj.allowed_assessors:
                return True
        return False

    def get_is_qa_officer(self,obj):
        #request = self.context['request']
        #return request.user.email in obj.qa_officers()
        return True

    #def get_fee_invoice_url(self,obj):
     #   return '/cols/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None

class ProposalSerializer(BaseProposalSerializer):
    #submitter = serializers.CharField(source='submitter.get_full_name')
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    application_type = serializers.CharField(source='application_type.name', read_only=True)

    def get_readonly(self,obj):
        return obj.can_user_view

    def get_submitter(self,obj):
        email_user = retrieve_email_user(obj.submitter)
        return email_user.get_full_name()

#class ProposalApplicantDetailsSerializer(serializers.ModelSerializer):
#
#    class Meta:
#        model = ProposalApplicantDetails
#        fields = (
#                'id',
#                'first_name',
#                )

class CreateProposalSerializer(BaseProposalSerializer):
    application_type_id = serializers.IntegerField(write_only=True, required=False)
    proposal_type_id = serializers.IntegerField(write_only=True, required=False)
    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type_id',
                'submitter',
                'org_applicant',
                'proposal_type_id',
                )
        read_only_fields=('id',)


class SaveRegistrationOfInterestSerializer(BaseProposalSerializer):

    class Meta:
        model = Proposal
        fields = (
                'id',
                'details_text',
                ## additional form fields
                'exclusive_use',
                'long_term_use',
                'consistent_purpose',
                'consistent_plan',
                'clearing_vegetation',
                'ground_disturbing_works',
                'heritage_site',
                'environmentally_sensitive',
                'wetlands_impact',
                'building_required',
                'significant_change',
                'aboriginal_site',
                'native_title_consultation',
                'mining_tenement',
                )
        read_only_fields=('id',)


class SaveProposalSerializer(BaseProposalSerializer):
    proxy_applicant = serializers.IntegerField(required=False)
    assigned_officer = serializers.IntegerField(required=False)

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'title',
                'customer_status',
                'processing_status',
                'applicant_type',
                'applicant',
                'org_applicant',
                'proxy_applicant',
                'submitter',
                'assigned_officer',
                'previous_application',
                'lodgement_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'reference',
                'lodgement_number',
                #'lodgement_sequence',
                'can_officer_process',
                'applicant_details',
                'details_text',
                )
        read_only_fields=('documents','requirements',)



class ApplicantSerializer(serializers.ModelSerializer):
    #from leaseslicensing.components.organisations.serializers import OrganisationAddressSerializer
    #address = OrganisationAddressSerializer(read_only=True)
    class Meta:
        model = Organisation
        fields = (
                    'id',
                    'name',
                    'abn',
                    #'address',
                    'email',
                    'phone_number',
                )


class ProposalReferralSerializer(serializers.ModelSerializer):
    #referral = serializers.CharField(source='referral.get_full_name')
    referral = serializers.CharField(source='referral_group.name')
    processing_status = serializers.CharField(source='get_processing_status_display')
    class Meta:
        model = Referral
        fields = '__all__'

class ProposalDeclinedDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalDeclinedDetails
        fields = '__all__'

class ProposalParkSerializer(BaseProposalSerializer):
    applicant = ApplicantSerializer()
    processing_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    submitter = serializers.CharField(source='submitter.get_full_name')
    application_type = serializers.CharField(source='application_type.name', read_only=True)
    licence_number = serializers.SerializerMethodField(read_only=True)
    licence_number_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proposal
        fields = (
                'id',
                'licence_number',
                'licence_number_id',
                'application_type',
                'approval_level',
                'title',
                'customer_status',
                'processing_status',
                'applicant',
                'proxy_applicant',
                'submitter',
                'lodgement_number',
                )

    def get_licence_number(self,obj):
        return obj.approval.lodgement_number

    def get_licence_number_id(self,obj):
        return obj.approval.id


class InternalProposalSerializer(BaseProposalSerializer):
    #applicant = ApplicantSerializer()
    applicant = serializers.CharField(read_only=True)
    org_applicant = OrganisationSerializer()
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    submitter = EmailUserAppViewSerializer()
    proposaldeclineddetails = ProposalDeclinedDetailsSerializer()
    assessor_mode = serializers.SerializerMethodField()
    can_edit_activities = serializers.SerializerMethodField()
    can_edit_period = serializers.SerializerMethodField()
    current_assessor = serializers.SerializerMethodField()
    latest_referrals = ProposalReferralSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    approval_level_document = serializers.SerializerMethodField()
    application_type = serializers.CharField(source='application_type.name', read_only=True)
    #qaofficer_referrals = QAOfficerReferralSerializer(many=True)
    reversion_ids = serializers.SerializerMethodField()
    assessor_assessment=ProposalAssessmentSerializer(read_only=True)
    referral_assessments=ProposalAssessmentSerializer(read_only=True, many=True)
    fee_invoice_url = serializers.SerializerMethodField()
    requirements_completed=serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'activity',
                'approval_level',
                'approval_level_document',
                'title',
                'customer_status',
                'processing_status',
                'review_status',
                'applicant',
                'org_applicant',
                'proxy_applicant',
                'submitter',
                'applicant_type',
                'assigned_officer',
                'assigned_approver',
                'previous_application',
                'get_history',
                'lodgement_date',
                #'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'assessor_mode',
                'current_assessor',
                'latest_referrals',
                'allowed_assessors',
                'proposed_issuance_approval',
                'proposed_decline_status',
                'proposaldeclineddetails',
                'permit',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'proposal_type',
                #'qaofficer_referrals',
                # tab field models
                'applicant_details',
                'other_details',
                'can_edit_activities',
                'can_edit_period',
                'reversion_ids',
                'assessor_assessment',
                'referral_assessments',
                'fee_invoice_url',
                #'fee_paid',
                'requirements_completed'
                )
        read_only_fields=('documents','requirements')

    def get_approval_level_document(self,obj):
        if obj.approval_level_document is not None:
            return [obj.approval_level_document.name,obj.approval_level_document._file.url]
        else:
            return obj.approval_level_document

    def get_assessor_mode(self,obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return {
            'assessor_mode': True,
            'has_assessor_mode': obj.has_assessor_mode(user),
            'assessor_can_assess': obj.can_assess(user),
            'assessor_level': 'assessor',
            'assessor_box_view': obj.assessor_comments_view(user)
        }

    def get_can_edit_period(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_edit_period(user)

    def get_readonly(self,obj):
        return True

    def get_requirements_completed(self,obj):
        return True

    def get_current_assessor(self,obj):
        return {
            'id': self.context['request'].user.id,
            'name': self.context['request'].user.get_full_name(),
            'email': self.context['request'].user.email
        }

    def get_reversion_ids(self,obj):
        return obj.reversion_ids[:5]

    def get_fee_invoice_url(self,obj):
        return '/cols/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None

class ProposalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')
    class Meta:
        model = ProposalUserAction
        fields = '__all__'

class ProposalLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = ProposalLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]

class SendReferralSerializer(serializers.Serializer):
    #email = serializers.EmailField()
    email_group = serializers.CharField()
    text = serializers.CharField(allow_blank=True)

class DTReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source='proposal.get_processing_status_display')
    application_type = serializers.CharField(source='proposal.application_type.name')
    referral_status = serializers.CharField(source='get_processing_status_display')
    proposal_lodgement_date = serializers.CharField(source='proposal.lodgement_date')
    proposal_lodgement_number = serializers.CharField(source='proposal.lodgement_number')
    submitter = serializers.SerializerMethodField()
    #egion = serializers.CharField(source='region.name', read_only=True)
    #referral = EmailUserSerializer()
    referral = serializers.CharField(source='referral_group.name')
    document = serializers.SerializerMethodField()
    can_user_process=serializers.SerializerMethodField()
    assigned_officer = serializers.CharField(source='assigned_officer.get_full_name', allow_null=True)
    class Meta:
        model = Referral
        fields = (
            'id',
            #'region',
            #'activity',
            'title',
            'applicant',
            'submitter',
            'processing_status',
            'application_type',
            'referral_status',
            'lodged_on',
            'proposal',
            'can_be_processed',
            'referral',
            'proposal_lodgement_date',
            'proposal_lodgement_number',
            'referral_text',
            'document',
            'assigned_officer',
            'can_user_process',
        )

    def get_submitter(self,obj):
        return EmailUserSerializer(obj.proposal.submitter).data

    # def get_document(self,obj):
    #     docs =  [[d.name,d._file.url] for d in obj.referral_documents.all()]
    #     return docs[0] if docs else None
    def get_document(self,obj):
        #doc = obj.referral_documents.last()
        return [obj.document.name, obj.document._file.url] if obj.document else None

    def get_can_user_process(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        if obj.can_process(user) and obj.can_be_completed:
            if obj.assigned_officer:
                if obj.assigned_officer == user:
                    return True
            else:
                return True
        return False



class RequirementDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequirementDocument
        fields = ('id', 'name', '_file')
        #fields = '__all__'

class ProposalRequirementSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    can_referral_edit=serializers.SerializerMethodField()
    can_district_assessor_edit=serializers.SerializerMethodField()
    requirement_documents = RequirementDocumentSerializer(many=True, read_only=True)
    class Meta:
        model = ProposalRequirement
        fields = (
            'id',
            'due_date',
            'free_requirement',
            'standard_requirement',
            'standard','order',
            'proposal',
            'recurrence',
            'recurrence_schedule',
            'recurrence_pattern',
            'requirement',
            'is_deleted',
            'copied_from',
            'referral_group',
            'can_referral_edit',
            'district_proposal',
            'district',
            'requirement_documents',
            'can_district_assessor_edit',
            'require_due_date',
            'copied_for_renewal',
            'notification_only',
        )
        read_only_fields = ('order','requirement', 'copied_from')

    def get_can_referral_edit(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_referral_edit(user)

    def get_can_district_assessor_edit(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_district_assessor_edit(user)

class ProposalStandardRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalStandardRequirement
        fields = ('id','code','text')

class ProposedApprovalSerializer(serializers.Serializer):
    expiry_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    start_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    details = serializers.CharField()
    cc_email = serializers.CharField(required=False,allow_null=True)

class PropedDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)

class OnHoldSerializer(serializers.Serializer):
    comment = serializers.CharField()


class AmendmentRequestSerializer(serializers.ModelSerializer):
    #reason = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = '__all__'

    #def get_reason (self,obj):
        #return obj.get_reason_display()
        #return obj.reason.reason

class AmendmentRequestDisplaySerializer(serializers.ModelSerializer):
    reason = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = '__all__'

    def get_reason (self,obj):
        #return obj.get_reason_display()
        return obj.reason.reason if obj.reason else None


class SearchKeywordSerializer(serializers.Serializer):
    number = serializers.CharField()
    id = serializers.IntegerField()
    type = serializers.CharField()
    applicant = serializers.CharField()
    #text = serializers.CharField(required=False,allow_null=True)
    text = serializers.JSONField(required=False)

class SearchReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()

class ReferralProposalSerializer(InternalProposalSerializer):
    def get_assessor_mode(self,obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        try:
            referral = Referral.objects.get(proposal=obj,referral=user)
        except:
            referral = None
        return {
            'assessor_mode': True,
            'assessor_can_assess': referral.can_assess_referral(user) if referral else None,
            'assessor_level': 'referral',
            'assessor_box_view': obj.assessor_comments_view(user)
        }

class ReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source='get_processing_status_display')
    latest_referrals = ProposalReferralSerializer(many=True)
    can_be_completed = serializers.BooleanField()
    can_process=serializers.SerializerMethodField()
    referral_assessment=ProposalAssessmentSerializer(read_only=True)
    application_type=serializers.CharField(read_only=True)
    allowed_assessors = EmailUserSerializer(many=True)
    current_assessor = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = '__all__'

    def get_current_assessor(self,obj):
        return {
            'id': self.context['request'].user.id,
            'name': self.context['request'].user.get_full_name(),
            'email': self.context['request'].user.email
        }

    # def __init__(self,*args,**kwargs):
    #     super(ReferralSerializer, self).__init__(*args, **kwargs)
    #     self.fields['proposal'] = ReferralProposalSerializer(context={'request':self.context['request']})
        

    def __init__(self,*args,**kwargs):
        super(ReferralSerializer, self).__init__(*args, **kwargs)
        try:    
            if kwargs.get('context')['view'].get_object().proposal.application_type.name == ApplicationType.TCLASS:
                self.fields['proposal'] = ReferralProposalSerializer(context={'request':self.context['request']})
            elif kwargs.get('context')['view'].get_object().proposal.application_type.name == ApplicationType.FILMING:
                self.fields['proposal'] = FilmingReferralProposalSerializer(context={'request':self.context['request']})
            elif kwargs.get('context')['view'].get_object().proposal.application_type.name == ApplicationType.EVENT:
                self.fields['proposal'] = EventReferralProposalSerializer(context={'request':self.context['request']})
        except:
            raise

    def get_can_process(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_process(user)
