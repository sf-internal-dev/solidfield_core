from backend.apps.core.services.technician_permission_service import delegate_permission_level, create_temporary_delegation, has_permission, list_effective_permissions, revoke_delegation, list_outgoing_delegations, list_incoming_delegations
from backend.apps.core.services.technician_registration_service import register_technician
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.edge_services.webhook_forwarder_service.publisher import publish_ui_messages



@api_view(["POST"])
def register_technician_api(request):
    data = request.data or {}
    # technician_operating = getattr(request, "technician_operating", None)

    username = data.get("username")
    social_name = data.get("social_name")
    technician_permission = data.get("technician_permission")

    technician, messages = register_technician(
            technician_operating=...,  # vai mapear para request.technician_operating depois
            username=username,
            social_name=social_name,
            technician_permission=technician_permission,
    )
    if messages:
        payloads = [get_error_payload(c) for c in messages]
        # eu vou provavelmente rever esse uso de tenant.id
        publish_ui_messages(
            technician_id=..., #technician_operating
            tenant_id=technician.tenant.id,
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "success": "Technician registered",
        "id": str(technician.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)
