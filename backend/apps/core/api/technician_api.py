from backend.apps.core.services.technician_permission_service import delegate_permission_level, create_temporary_delegation, has_permission, list_effective_permissions, revoke_delegation, list_outgoing_delegations, list_incoming_delegations
from backend.apps.core.services.technician_registration_service import register_technician
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(["POST"])
def register_technician_api(request):
    data = request.data or {}
    username = data.get("username")
    social_name = data.get("social_name")
    technician_permission = data.get("technician_permission")

    messages_to_publish = []
    technician, errors = register_technician(
            technician_operating=request.user,  # ou mapeia p/ teu Technician-operador
            username=username,
            social_name=social_name,
            technician_permission=technician_permission,
    )
    if errors:
        for error in errors:
            messages_to_publish.append(get_error_payload(error))
            # tem que fazer a publicação desses erros com algum serviço, provavelmente vai ser no corex
        return Response({
        }, status=status.HTTP_409_CONFLICT)

    return Response({
        "id": str(technician.id),
        "username": technician.username,
        "social_name": technician.social_name,
        "technician_permission": technician.technician_permission,
        "is_active": technician.is_active,
    }, status=status.HTTP_201_CREATED)
