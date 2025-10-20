from rest_framework import serializers
from backend.apps.core.models import Technician, CompanyTenant, TechniciansAggroupment

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyTenant
        fields = ["id", "name"]  

class TechniciansAggroupmentSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True) 

    class Meta:
        model = TechniciansAggroupment
        fields = ["id", "tag", "allowed_to_operate", "created_at", "updated_at"]

class TechnicianSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True) 
    aggroupment = TechniciansAggroupmentSerializer(read_only=True)

    class Meta:
        model = Technician
        fields = ["id", "username", "social_name", "technician_permission", "aggroupment", "is_active", "created_at", "updated_at"]
