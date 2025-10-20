from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.apps.core.models import CompanyTenant
from backend.apps.core.api.serializers.core_serializers import TenantSerializer

@api_view(["GET"])
def list_tenants_api(request):
    tenants = CompanyTenant.objects.all()

    serializer = TenantSerializer(tenants, many=True)
    return Response({"tenants": serializer.data}, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_tenant_api(request, tenant_id):
    try:
        tenant = CompanyTenant.objects.get(id=tenant_id)
    except CompanyTenant.DoesNotExist:
        return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TenantSerializer(tenant)
    return Response({"tenant": serializer.data}, status=status.HTTP_200_OK)