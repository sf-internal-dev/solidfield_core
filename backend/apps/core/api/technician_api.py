import hashlib
from backend.apps.core.services.technician_permission_service import delegate_permission_level, create_temporary_delegation, has_permission, list_effective_permissions, revoke_delegation, list_outgoing_delegations, list_incoming_delegations
from backend.apps.core.services.technician_registration_service import register_technician
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip


@api_view(["POST"])
def register_technician_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)

    username = data.get("username")
    social_name = data.get("social_name")
    technician_permission = data.get("technician_permission")

    technician, messages = register_technician(
            technician_operating=technician_operating,
            username=username,
            social_name=social_name,
            technician_permission=technician_permission,
    )
    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician is not None and getattr(technician, "tenant", None) is not None:
            tenant_id = getattr(technician.tenant, "id", None)
        elif technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        manager_account_operating = getattr(request.user, "id", None)

        correlation = publish_ui_messages(
            payloads=payloads,
            technician_operating_id=technician_operating,
            recipient_technician_id=technician_operating,
            manager_account_operating_id=manager_account_operating,
            recipient_session_id=session_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Technician registered",
        "id": str(technician.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)
