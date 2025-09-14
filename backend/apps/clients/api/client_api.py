from backend.apps.clients.services.client_registration_service import register_client_address, create_or_update_client
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.edge_services.webhook_forwarder_service.publisher import publish_ui_messages
from backend.common.schemas.error_messages_schema import get_error_payload


@api_view(["POST"])
def register_client_api(request):
    data = request.data or {}
    # technician_operating = getattr(request, "technician_operating", None)
    
    # client = data.get("client")
    person_type = data.get("person_type")
    name = data.get("name")
    document_id = data.get("document_id")
    contact_name = data.get("contact_name")
    phone = data.get("phone")
    email = data.get("email")
    country = data.get("country")

    client, messages = create_or_update_client(
        person_type = person_type,
        name = name,
        document_id = document_id,
        contact_name = contact_name,
        phone = phone,
        email = email,
        country= country
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]
        # eu vou provavelmente rever esse uso de tenant.id
        publish_ui_messages(
            technician_id=..., #technician_operating
            tenant_id=...,#technician_operating.tenant.id
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "id": str(client.id),
        "name": client.name,
        "document_id": client.document_id,
        "contact_name": client.contact_name,
        "phone": client.phone,
        "email": client.email
    }, status=status.HTTP_201_CREATED)