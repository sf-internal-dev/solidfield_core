from backend.apps.clients.services.feedback_request_generation_service import create_feedback_link, create_client_feedback
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.orders.models import WorkOrder
from backend.apps.clients.models import Client

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
