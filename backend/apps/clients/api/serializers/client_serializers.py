from rest_framework import serializers
from backend.apps.clients.models import Client, ClientAddress, ClientFeedback
from backend.apps.core.api.serializers.core_serializers import TenantSerializer

class ClientSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True) 

    class Meta:
        model = Client
        fields = ["id", "person_type", "name", "document_id", "contact_name", "phone", "email", "created_at", "is_active"]  

class TechniciansAggroupmentSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True) 

    class Meta:
        model = TechniciansAggroupment
        fields = ["id", "tag", "allowed_to_operate", "created_at", "updated_at"]
