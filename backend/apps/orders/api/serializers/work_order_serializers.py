from rest_framework import serializers
from backend.apps.orders.models import WorkOrder, WorkOrderStatusHistory, WorkOrderDownloadLink
from backend.apps.core.api.serializers.core_serializers import TechnicianSerializer, TenantSerializer


class WorkOrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = TechnicianSerializer(read_only=True)

    class Meta:
        model = WorkOrderStatusHistory
        fields = [
            'id', 'status', 'changed_by', 'notes', 'created_at'
        ]


class WorkOrderDownloadLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderDownloadLink
        fields = [
            'id', 'key', 'purpose', 'expires_at', 'created_at'
        ]


class WorkOrderSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    assigned_to = TechnicianSerializer(read_only=True)
    created_by = TechnicianSerializer(read_only=True)
    status_history = WorkOrderStatusHistorySerializer(source='workorderstatushistory_set', many=True, read_only=True)
    download_links = WorkOrderDownloadLinkSerializer(source='workorderdownloadlink_set', many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'identifier', 'title', 'description', 'status', 'priority',
            'tenant', 'assigned_to', 'created_by', 'due_date', 'location',
            'notes', 'status_history', 'download_links', 'created_at', 'updated_at'
        ]


class WorkOrderListSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    assigned_to = TechnicianSerializer(read_only=True)
    created_by = TechnicianSerializer(read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'identifier', 'title', 'description', 'status', 'priority',
            'tenant', 'assigned_to', 'created_by', 'due_date', 'location',
            'created_at', 'updated_at'
        ]
