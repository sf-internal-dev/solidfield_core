from rest_framework import serializers
from backend.apps.clients.models import Client, ClientAddress, ClientFeedback
from backend.apps.core.api.serializers.core_serializers import TenantSerializer

class ClientSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True) 

    class Meta:
        model = Client
        fields = ["id", "person_type", "name", "document_id", "contact_name", "phone", "email", "created_at", "is_active"]  


class ClientAddressSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True) 

    class Meta:
        model = ClientAddress
        fields = ["id", "label", "street", "number", "complement", "neighborhood", "city", "state", "postal_code", "gps_latitude", "gps_longitude"]
