from backend.apps.core.services.tenant_service import register_tenant, register_tenant_branding, update_tenant, get_tenant_workflow, update_tenant_workflow
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
import hashlib
from backend.apps.core.models import Technician, CompanyTenant

@api_view(["POST"])
def register_tenant_api(request):
    data = request.data or {}
    manager_account_operating = getattr(request, "manager_account_operating", None)

    name                  = data.get("name")
    slug                  = data.get("slug")
    tenant_code           = data.get("tenant_code")
    primary_contact_name  = data.get("primary_contact_name")
    primary_contact_email = data.get("primary_contact_email")
    primary_contact_phone = data.get("primary_contact_phone")
    billing_account_id    = data.get("billing_account_id")
    owner_id                = data.get("owner")

    owner = None
    if owner_id is not None:
        owner = Technician.objects.get(pk=owner_id)


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

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            session_id=session_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Tenant registered",
        "id": str(tenant.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)



@api_view(["POST"])
def register_tenant_branding_api(request):
    data = request.data or {}
    manager_account_operating = getattr(request, "manager_account_operating", None)

    tenant_id       = data.get("tenant")
    tenant = None
    if tenant_id is not None:
        tenant = CompanyTenant.objects.get(pk=tenant_id)

    logo          = data.get("logo")
    color_primary = data.get("color_primary")

    tenant_update, messages = register_tenant_branding(
        tenant=tenant,
        logo=logo,
        color_primary=color_primary
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        correlation = publish_ui_messages(
                manager_account_operating_id=manager_account_operating,
                session_id=session_id,
                client_ip=client_ip,
                client_fingerprint=client_fingerprint,
                payloads=payloads,
                source="django_api",
            )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "success": "Tenant branding registered",
        "id": str(tenant_update.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)


@api_view(["PUT"])
def update_tenant_api(request, tenant_id):
    data = request.data or {}
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Extract update data
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "slug" in data:
        update_data["slug"] = data["slug"]
    if "primary_contact_name" in data:
        update_data["primary_contact_name"] = data["primary_contact_name"]
    if "primary_contact_email" in data:
        update_data["primary_contact_email"] = data["primary_contact_email"]
    if "primary_contact_phone" in data:
        update_data["primary_contact_phone"] = data["primary_contact_phone"]
    if "billing_account_id" in data:
        update_data["billing_account_id"] = data["billing_account_id"]
    if "country" in data:
        update_data["country"] = data["country"]
    if "locale" in data:
        update_data["locale"] = data["locale"]
    if "timezone" in data:
        update_data["timezone"] = data["timezone"]
    if "color_primary" in data:
        update_data["color_primary"] = data["color_primary"]
    if "logo" in data:
        update_data["logo"] = data["logo"]
    if "is_active" in data:
        update_data["is_active"] = data["is_active"]

    tenant, messages = update_tenant(
        tenant_id=tenant_id,
        **update_data
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            session_id=session_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            payloads=payloads,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Tenant updated",
        "id": str(tenant.id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_tenant_workflow_api(request, tenant_id):
    manager_account_operating = getattr(request, "manager_account_operating", None)

    workflow, messages = get_tenant_workflow(tenant_id=tenant_id)

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            session_id=session_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            payloads=payloads,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Tenant workflow retrieved",
        "workflow": workflow,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_tenant_workflow_api(request, tenant_id):
    data = request.data or {}
    manager_account_operating = getattr(request, "manager_account_operating", None)

    workflow_data = data.get("workflow", {})

    success, messages = update_tenant_workflow(
        tenant_id=tenant_id,
        workflow_data=workflow_data
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            session_id=session_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            payloads=payloads,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Tenant workflow updated",
        "messages": messages,
    }, status=status.HTTP_200_OK)


