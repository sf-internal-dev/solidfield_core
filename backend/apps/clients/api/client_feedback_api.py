from backend.apps.clients.services.feedback_request_generation_service import create_feedback_link, create_client_feedback, list_feedback, get_feedback_analytics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.orders.models import WorkOrder
from backend.apps.clients.models import Client
from backend.apps.clients.api.serializers.client_serializers import ClientFeedbackSerializer
from datetime import datetime

@api_view(["POST"])
def create_feedback_link_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)
    work_order_id = data.get("work_order")

    work_order = None
    if work_order_id is not None:
        work_order = WorkOrder.objects.get(pk=work_order_id)

    feedback_link, messages = create_feedback_link(
        technician_operating=technician_operating,
        work_order = work_order
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
        "success": "Feedback Link registered",
        "feedback_link_id": str(feedback_link.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def create_client_feedback_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    work_order_id = data.get("work_order")

    work_order = None
    if work_order_id is not None:
        work_order = WorkOrder.objects.get(pk=work_order_id)

    client_id = data.get("client")

    client = None
    if client_id is not None:
        client = Client.objects.get(pk=client_id)

    client_name = data.get("client_name")
    client_email = data.get("client_email")
    stars = data.get("stars")
    comment = data.get("comment")
    strenghts = data.get("strenghts")

    client_feedback, messages = create_client_feedback(
        technician_operating=technician_operating,
        work_order=work_order,
        client=client,
        client_name=client_name,
        client_email=client_email,
        stars=stars,
        comment=comment,
        strengths=strenghts
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
        "success": "Client Feedback registered",
        "client_feedback_id": str(client_feedback.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def list_feedback_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Get query parameters
    work_order_id = request.GET.get("work_order_id")
    client_id = request.GET.get("client_id")
    min_stars = request.GET.get("min_stars")
    max_stars = request.GET.get("max_stars")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    # Convert parameters
    work_order_id = int(work_order_id) if work_order_id else None
    client_id = int(client_id) if client_id else None
    min_stars = int(min_stars) if min_stars else None
    max_stars = int(max_stars) if max_stars else None
    
    # Parse dates
    date_from_parsed = None
    date_to_parsed = None
    if date_from:
        try:
            date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            pass

    feedback_list, messages = list_feedback(
        technician_operating=technician_operating,
        work_order_id=work_order_id,
        client_id=client_id,
        min_stars=min_stars,
        max_stars=max_stars,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
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

    # Serialize feedback
    serializer = ClientFeedbackSerializer(feedback_list, many=True)

    return Response({
        "success": "Feedback retrieved",
        "feedback": serializer.data,
        "count": len(feedback_list),
        "limit": limit,
        "offset": offset,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_feedback_analytics_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Get query parameters
    work_order_id = request.GET.get("work_order_id")
    client_id = request.GET.get("client_id")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    # Convert parameters
    work_order_id = int(work_order_id) if work_order_id else None
    client_id = int(client_id) if client_id else None
    
    # Parse dates
    date_from_parsed = None
    date_to_parsed = None
    if date_from:
        try:
            date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            pass

    analytics, messages = get_feedback_analytics(
        technician_operating=technician_operating,
        work_order_id=work_order_id,
        client_id=client_id,
        date_from=date_from_parsed,
        date_to=date_to_parsed
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
        "success": "Feedback analytics retrieved",
        "analytics": analytics,
        "messages": messages,
    }, status=status.HTTP_200_OK)
