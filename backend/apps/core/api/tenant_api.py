from backend.apps.core.services.tenant_service import register_tenant, register_tenant_branding
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.edge_services.webhook_forwarder_service.publisher import publish_ui_messages

'''
class CompanyTenant(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True) 
    tenant_code = models.CharField(max_length=10,unique=True,db_index=True,editable=False, validators=[validate_tenant_core])
    is_active = models.BooleanField(default=True)
    
    primary_contact_name = models.CharField(max_length=100, blank=True)
    primary_contact_email = models.EmailField(blank=True)
    primary_contact_phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    billing_account_id = models.CharField(max_length=100, blank=True, null=True) 

    owner = models.OneToOneField(
        "core.AccountHolderUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_tenant"
    )

    locale = models.CharField(max_length=10, default="en-US")
    timezone = models.CharField(max_length=50, default="America/Los_Angeles")

    logo = models.ImageField(upload_to="tenant_logos/", null=True, blank=True)
    color_primary = models.CharField(max_length=7, default="#000000") 
'''

@api_view(["POST"])
def register_tenant_api(request):
    data = request.data or {}
    """ I will probably create a request for billing account id for this case as 
    it is a operation that does not imply a technician registered"""
    # billing_account_operating = getattr(request, "billing_account_operating", None)

    name                  = data.get("name")
    slug                  = data.get("slug")
    tenant_code           = data.get("")
    primary_contact_name  = data.get("primary_contact_name")
    primary_contact_email = data.get("primary_contact_email")
    primary_contact_phone = data.get("primary_contact_phone")
    billing_account_id    = data.get("billing_account_id")
    owner                 = data.get("owner")
    country               = data.get("country")
    locale                = data.get("locale")
    timezone              = data.get("timezone")

    tenant, messages = register_tenant(
            billing_account_operating=...,  # vai mapear para request.billing_account_operating depois
            name=name,
            slug=slug,
            tenant_code=tenant_code,
            primary_contact_name=primary_contact_name,
            primary_contact_email=primary_contact_email,
            primary_contact_phone=primary_contact_phone,
            billing_account_id=billing_account_id,
            owner=owner,
            country=country,
            locale=locale,
            timezone=timezone
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]
        # eu vou provavelmente rever esse uso de tenant.id
        """ Vou precisar esse publish_ui_messages por que não vai poder receber technician id"""
        publish_ui_messages(
            # technician_id=..., #technician_operating
            # tenant_id=technician.tenant.id,
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Tenant registered",
        "id": str(tenant.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)



@api_view(["POST"])
def register_tenant_branding_api(request):
    pass

