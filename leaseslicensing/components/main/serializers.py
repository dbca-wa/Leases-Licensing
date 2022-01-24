from rest_framework import serializers
from django.db.models import Sum, Max
from leaseslicensing.components.main.models import (
        CommunicationsLogEntry, 
        RequiredDocument, Question, GlobalSettings, ApplicationType, MapLayer, MapColumn,
        )
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from datetime import datetime, date
#from leaseslicensing.components.proposals.serializers import ProposalTypeSerializer

class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=EmailUser.objects.all(),required=False)
    documents = serializers.SerializerMethodField()
    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'proposal'
            'documents'
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]


class ApplicationTypeSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()
    #regions = RegionSerializer(many=True)
    #activity_app_types = ActivitySerializer(many=True)
    #tenure_app_types = TenureSerializer(many=True)

    class Meta:
        model = ApplicationType
        #fields = ('id', 'name', 'activity_app_types', 'tenure_app_types')
        #fields = ('id', 'name', 'tenure_app_types')
        fields = '__all__'
        extra_fields = ['name_display']

    def get_name_display(self, obj):
        return obj.get_name_display()


class GlobalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSettings
        fields = ('key', 'value')


class RequiredDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredDocument
        fields = ('id', 'park','activity', 'question')


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'answer_one', 'answer_two', 'answer_three', 'answer_four','correct_answer', 'correct_answer_value')


class BookingSettlementReportSerializer(serializers.Serializer):
    date = serializers.DateTimeField(input_formats=['%d/%m/%Y'])


class OracleSerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=['%d/%m/%Y','%Y-%m-%d'])
    override = serializers.BooleanField(default=False)


class MapColumnSerializer(serializers.ModelSerializer):

    class Meta:
        model = MapColumn
        fields = (
            'name',
            'option_for_internal',
            'option_for_external',
        )


class MapLayerSerializer(serializers.ModelSerializer):
    layer_full_name = serializers.SerializerMethodField()
    layer_group_name = serializers.SerializerMethodField()
    layer_name = serializers.SerializerMethodField()
    columns = MapColumnSerializer(many=True)

    class Meta:
        model = MapLayer
        fields = (
            'id',
            'display_name',
            'layer_full_name',
            'layer_group_name',
            'layer_name',
            'display_all_columns',
            'columns',
        )
        read_only_fields=('id',)

    def get_layer_full_name(self, obj):
        return obj.layer_name.strip()

    def get_layer_group_name(self, obj):
        return obj.layer_name.strip().split(':')[0]

    def get_layer_name(self, obj):
        return obj.layer_name.strip().split(':')[1]
