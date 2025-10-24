from backend.apps.clients.services.client_registration_service import register_client_address, create_or_update_client, update_client, delete_client, search_clients
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.clients.models import Client
from backend.apps.clients.api.serializers.client_serializers import ClientSerializer

@api_view(["POST"])
def register_client_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # client = data.get("client")
    person_type = data.get("person_type")
    name = data.get("name")
    document_id = data.get("document_id")
    contact_name = data.get("contact_name")
    phone = data.get("phone")
    email = data.get("email")
    country = data.get("country")

    client, messages = create_or_update_client(
        technician_operating=technician_operating,
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

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            technician_operating_id=technician_operating,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            session_id=session_id,
            tenant_id=tenant_id,
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "success": "Client registered",
        "client_id": str(client.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def register_client_adress_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    client_id = data.get("client")

    client = None
    if client_id is not None:
        client = Client.objects.get(pk=client_id)

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
        technician_operating= technician_operating,
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

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            technician_operating_id=technician_operating,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            session_id=session_id,
            tenant_id=tenant_id,
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    return Response({
        "success": "Client adress registered",
        "client_adress_id":  str(client_adress.id),
        "messages": messages,
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)


@api_view(["PUT"])
def update_client_api(request, client_id):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Extract update data
    update_data = {}
    if "person_type" in data:
        update_data["person_type"] = data["person_type"]
    if "name" in data:
        update_data["name"] = data["name"]
    if "document_id" in data:
        update_data["document_id"] = data["document_id"]
    if "contact_name" in data:
        update_data["contact_name"] = data["contact_name"]
    if "phone" in data:
        update_data["phone"] = data["phone"]
    if "email" in data:
        update_data["email"] = data["email"]
    if "country" in data:
        update_data["country"] = data["country"]
    if "is_active" in data:
        update_data["is_active"] = data["is_active"]

    client, messages = update_client(
        technician_operating=technician_operating,
        client_id=client_id,
        **update_data
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            technician_operating_id=technician_operating,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            session_id=session_id,
            tenant_id=tenant_id,
            payloads=payloads,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Client updated",
        "client_id": str(client.id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_client_api(request, client_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    success, messages = delete_client(
        technician_operating=technician_operating,
        client_id=client_id
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            technician_operating_id=technician_operating,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            session_id=session_id,
            tenant_id=tenant_id,
            payloads=payloads,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Client deleted",
        "client_id": str(client_id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def search_clients_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Get query parameters
    query = request.GET.get("q")
    person_type = request.GET.get("person_type")
    is_active = request.GET.get("is_active")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    # Convert is_active to boolean if provided
    if is_active is not None:
        is_active = is_active.lower() in ['true', '1', 'yes']

    clients, messages = search_clients(
        technician_operating=technician_operating,
        query=query,
        person_type=person_type,
        is_active=is_active,
        limit=limit,
        offset=offset
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            technician_operating_id=technician_operating,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            session_id=session_id,
            tenant_id=tenant_id,
            payloads=payloads,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # Serialize clients
    serializer = ClientSerializer(clients, many=True)

    return Response({
        "success": "Clients retrieved",
        "clients": serializer.data,
        "count": len(clients),
        "limit": limit,
        "offset": offset,
        "query": query,
        "messages": messages,
    }, status=status.HTTP_200_OK)