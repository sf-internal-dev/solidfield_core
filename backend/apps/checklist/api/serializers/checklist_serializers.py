from rest_framework import serializers
from backend.apps.checklist.models import Checklist, ChecklistItemAnswer, ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.api.serializers.core_serializers import TechnicianSerializer, TenantSerializer


class ChecklistItemAnswerSerializer(serializers.ModelSerializer):
    item_template_id = serializers.IntegerField(source='item_template.id', read_only=True)
    question = serializers.CharField(source='item_template.question', read_only=True)
    answer_type = serializers.CharField(source='item_template.answer_type', read_only=True)
    required = serializers.BooleanField(source='item_template.required', read_only=True)

    class Meta:
        model = ChecklistItemAnswer
        fields = [
            'id', 'item_template_id', 'question', 'answer_type', 'required',
            'answer_bool', 'answer_texto', 'answer_number', 'answer_choice', 'note',
            'created_at', 'updated_at'
        ]


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)

    class Meta:
        model = ChecklistTemplate
        fields = ['id', 'name', 'service_type', 'version', 'is_global', 'tenant', 'created_at', 'updated_at']


class ChecklistSerializer(serializers.ModelSerializer):
    template = ChecklistTemplateSerializer(read_only=True)
    filled_by = TechnicianSerializer(read_only=True)
    work_order_id = serializers.IntegerField(source='work_order.id', read_only=True)
    work_order_identifier = serializers.CharField(source='work_order.identifier', read_only=True)

    class Meta:
        model = Checklist
        fields = [
            'id', 'template', 'filled_by', 'work_order_id', 'work_order_identifier',
            'status', 'created_at', 'updated_at'
        ]


class ChecklistDetailSerializer(serializers.ModelSerializer):
    template = ChecklistTemplateSerializer(read_only=True)
    filled_by = TechnicianSerializer(read_only=True)
    work_order_id = serializers.IntegerField(source='work_order.id', read_only=True)
    work_order_identifier = serializers.CharField(source='work_order.identifier', read_only=True)
    answers = ChecklistItemAnswerSerializer(source='checklistitemanswer_set', many=True, read_only=True)

    class Meta:
        model = Checklist
        fields = [
            'id', 'template', 'filled_by', 'work_order_id', 'work_order_identifier',
            'status', 'answers', 'created_at', 'updated_at'
        ]
