import hashlib

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.apps.core.services.offline_sync_service import (
    enqueue_offline_sync_item,
    list_my_offline_sync_queue,
    process_offline_sync_item,
)
from backend.common.schemas.error_messages_schema import get_error_payload
from backend.publisher import get_client_ip, publish_ui_messages


def _error_response(request, messages, technician_operating, manager_account_operating):
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


@api_view(["POST"])
def enqueue_offline_sync_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    if technician_operating is None:
        return Response(
            {"codes": ["technician_operating_required"], "correlation_id": None},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    payload = data.get("payload")
    client_mutation_id = data.get("client_mutation_id")
    queue_owner_id = data.get("queue_owner_technician_id")

    queue_owner = None
    if queue_owner_id is not None:
        from backend.apps.core.models import Technician

        try:
            queue_owner = Technician.objects.get(
                pk=int(queue_owner_id),
                tenant_id=technician_operating.tenant_id,
            )
        except (Technician.DoesNotExist, ValueError, TypeError):
            return _error_response(
                request,
                ["queue_owner_not_found"],
                technician_operating,
                manager_account_operating,
            )

    row, messages = enqueue_offline_sync_item(
        technician_operating=technician_operating,
        payload=payload,
        client_mutation_id=client_mutation_id,
        queue_owner=queue_owner,
    )
    if messages:
        return _error_response(request, messages, technician_operating, manager_account_operating)

    return Response(
        {
            "success": "offline_sync_enqueued",
            "queue_id": str(row.id),
            "status": row.status,
            "client_mutation_id": row.client_mutation_id,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def list_offline_sync_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    if technician_operating is None:
        return Response(
            {"codes": ["technician_operating_required"], "correlation_id": None},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    status_filter = request.GET.get("status")
    try:
        limit = int(request.GET.get("limit", 50))
        offset = int(request.GET.get("offset", 0))
    except (TypeError, ValueError):
        limit, offset = 50, 0

    rows, messages = list_my_offline_sync_queue(
        technician_operating=technician_operating,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    if messages:
        return _error_response(request, messages, technician_operating, manager_account_operating)

    data = [
        {
            "id": r.id,
            "status": r.status,
            "client_mutation_id": r.client_mutation_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "synced_at": r.synced_at.isoformat() if r.synced_at else None,
            "payload": r.payload,
        }
        for r in rows
    ]
    return Response({"success": "ok", "items": data, "count": len(data)}, status=status.HTTP_200_OK)


@api_view(["POST"])
def process_offline_sync_api(request, queue_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    if technician_operating is None:
        return Response(
            {"codes": ["technician_operating_required"], "correlation_id": None},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    final_status, messages = process_offline_sync_item(
        technician_operating=technician_operating,
        queue_id=int(queue_id),
    )

    if messages and final_status is None:
        if "queue_item_not_found" in messages:
            return Response({"codes": messages, "correlation_id": None}, status=status.HTTP_404_NOT_FOUND)
        return _error_response(request, messages, technician_operating, manager_account_operating)

    if messages and final_status == "conflict":
        return _error_response(request, messages, technician_operating, manager_account_operating)

    return Response(
        {
            "success": "offline_sync_processed",
            "queue_id": str(queue_id),
            "status": final_status,
        },
        status=status.HTTP_200_OK,
    )
