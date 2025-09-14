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
        technician_operating=..., #technician_operating
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

@api_view(["POST"])
def register_client_adress_api(request):
    data = request.data or {}
    # technician_operating = getattr(request, "technician_operating", None)
    
    client = data.get("client")
    label = data.get("label")
    number = data.get("number")
    complement = data.get("complement")
    neighborhood = data.get("neighborhood")
    city = data.get("city")
    state = data.get("state")
    postal_code = data.get("postal_code")
    
    gps_latitude = data.get("gps_latitude")
    gps_longitude = data.get("gps_longitude")


    client_adress, messages = register_client_address(
        technician_operating= ..., #technician_operating
        client = client,
        label = label,
        number = number,
        complement= complement,
        neighborhood= neighborhood,
        city = city,
        state = state, 
        postal_code = postal_code,
        gps_latitude = gps_latitude,
        gps_longitude = gps_longitude
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
        return Response({"messages": messages}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "success": "Client adress registered",
        "client_adress_id": client_adress.id,
        "messages": messages,
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)