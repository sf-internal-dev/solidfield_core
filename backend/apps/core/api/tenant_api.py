from backend.apps.core.services.tenant_service import register_tenant, register_tenant_branding
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages

@api_view(["POST"])
def register_tenant_api(request):
    data = request.data or {}
    manager_account_operating = getattr(request, "manager_account_operating", None)

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
            billing_account_operating=manager_account_operating,
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
    data = request.data or {}

    tenant        = data.get("tenant")
    logo          = data.get("logo")
    color_primary = data.get("color_primary")

    tenant_update, messages = register_tenant_branding(
        tenant=tenant,
        logo=logo,
        color_primary=color_primary
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]
        publish_ui_messages(
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "success": "Tenant branding registered",
        "id": str(tenant_update.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)


