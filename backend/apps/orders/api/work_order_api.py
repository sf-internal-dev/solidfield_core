from backend.apps.orders.services.work_order_identifier_service import create_work_order_with_identifier
from backend.apps.orders.services.work_order_management_service import list_work_orders, get_work_order, update_work_order, assign_work_order, get_work_order_status_history
from backend.apps.orders.services.work_order_download_service import create_work_order_download_link_with_key
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.core.models import CompanyTenant
from backend.apps.orders.models import WorkOrder
from backend.apps.orders.api.serializers.work_order_serializers import WorkOrderSerializer, WorkOrderListSerializer
from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.types import OpenApiTypes
from backend.apps.apis.spectacular_public import TAG_WORK_ORDER, schema_error_422

_WO_JSON = {"type": "object", "additionalProperties": True}
_WO_PATH_ID = OpenApiParameter("work_order_id", OpenApiTypes.INT, OpenApiParameter.PATH, required=True)
_UPDATE_BODY = {
    "application/json": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "nullable": True},
            "description": {"type": "string", "nullable": True},
            "priority": {"type": "string", "nullable": True},
            "status": {"type": "string", "nullable": True},
            "assigned_to": {"type": "integer", "nullable": True},
            "due_date": {"type": "string", "format": "date-time", "nullable": True},
            "location": {"type": "string", "nullable": True},
            "notes": {"type": "string", "nullable": True},
        },
    }
}


@extend_schema(
    tags=[TAG_WORK_ORDER],
    operation_id="publicV1WorkOrderCreate",
    summary="Creates a work order (trip / service order)",
    request={
        "application/json": {
            "type": "object",
            "properties": {"company": {"type": "integer", "nullable": True}},
        }
    },
    responses={201: _WO_JSON, 422: schema_error_422()},
)
@api_view(["POST"])
def create_work_order_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)
    company_id = data.get("company")

    company = None
    if company_id is not None:
        company = CompanyTenant.objects.get(pk=company_id)

    work_order, messages = create_work_order_with_identifier(
        company=company,
        created_by=technician_operating,
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
        "success": "Work Order registered",
        "work_order_id":  str(work_order.id),
        "messages": messages,
        # I might make the register functions return a payload of the data
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def create_work_order_download_link_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    work_order_id = data.get("work_order")

    work_order = None
    if work_order_id is not None:
        work_order = WorkOrder.objects.get(pk=work_order_id)

    days = data.get("days")

    work_order_download_link, messages = create_work_order_download_link_with_key(
        technician_operating=technician_operating,
        work_order=work_order,
        purpose=data.get("purpose", "general"),
        technician=technician_operating
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
        "success": "Work Order Download Link registered",
        "work_order_download_link_id":  str(work_order_download_link.id),
        "messages": messages,
        # I might make the register functions return a payload of the data
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=[TAG_WORK_ORDER],
    operation_id="publicV1WorkOrderList",
    summary="Lists work orders",
    parameters=[
        OpenApiParameter("technician_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("status", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("tenant_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY),
    ],
    responses={200: _WO_JSON, 422: schema_error_422()},
)
@api_view(["GET"])
def list_work_orders_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Get query parameters
    technician_id = request.GET.get("technician_id")
    status_filter = request.GET.get("status")
    tenant_id = request.GET.get("tenant_id")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    # Convert string IDs to integers if provided
    technician_id = int(technician_id) if technician_id else None
    tenant_id = int(tenant_id) if tenant_id else None

    work_orders, messages = list_work_orders(
        technician_operating=technician_operating,
        technician_id=technician_id,
        status=status_filter,
        tenant_id=tenant_id,
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

    # Serialize work orders
    serializer = WorkOrderListSerializer(work_orders, many=True)

    return Response({
        "success": "Work orders retrieved",
        "work_orders": serializer.data,
        "count": len(work_orders),
        "limit": limit,
        "offset": offset,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_WORK_ORDER],
    operation_id="publicV1WorkOrderRetrieve",
    summary="Retrieves a work order by id",
    parameters=[_WO_PATH_ID],
    responses={200: _WO_JSON, 422: schema_error_422()},
)
@api_view(["GET"])
def get_work_order_api(request, work_order_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    work_order, messages = get_work_order(
        technician_operating=technician_operating,
        work_order_id=work_order_id
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

    # Serialize work order with detailed information
    serializer = WorkOrderSerializer(work_order)

    return Response({
        "success": "Work order retrieved",
        "work_order": serializer.data,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_WORK_ORDER],
    operation_id="publicV1WorkOrderUpdate",
    summary="Updates a work order",
    parameters=[_WO_PATH_ID],
    request=_UPDATE_BODY,
    responses={200: _WO_JSON, 422: schema_error_422()},
)
@api_view(["PUT"])
def update_work_order_api(request, work_order_id):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Extract update data
    update_data = {}
    if "title" in data:
        update_data["title"] = data["title"]
    if "description" in data:
        update_data["description"] = data["description"]
    if "priority" in data:
        update_data["priority"] = data["priority"]
    if "status" in data:
        update_data["status"] = data["status"]
    if "assigned_to" in data:
        update_data["assigned_to"] = data["assigned_to"]
    if "due_date" in data:
        update_data["due_date"] = data["due_date"]
    if "location" in data:
        update_data["location"] = data["location"]
    if "notes" in data:
        update_data["notes"] = data["notes"]

    work_order, messages = update_work_order(
        technician_operating=technician_operating,
        work_order_id=work_order_id,
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
        "success": "Work order updated",
        "work_order_id": str(work_order.id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_WORK_ORDER],
    operation_id="publicV1WorkOrderAssign",
    summary="Assigns a work order to a technician",
    parameters=[_WO_PATH_ID],
    request={
        "application/json": {
            "type": "object",
            "required": ["technician_id"],
            "properties": {"technician_id": {"type": "integer"}},
        }
    },
    responses={
        200: _WO_JSON,
        400: {"type": "object", "properties": {"error": {"type": "string"}}},
        422: schema_error_422(),
    },
)
@api_view(["POST"])
def assign_work_order_api(request, work_order_id):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    technician_id = data.get("technician_id")
    if not technician_id:
        return Response({"error": "technician_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    success, messages = assign_work_order(
        technician_operating=technician_operating,
        work_order_id=work_order_id,
        technician_id=technician_id
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
        "success": "Work order assigned successfully",
        "work_order_id": str(work_order_id),
        "technician_id": str(technician_id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_WORK_ORDER],
    operation_id="publicV1WorkOrderStatusHistory",
    summary="Work order status history",
    parameters=[_WO_PATH_ID],
    responses={200: _WO_JSON, 422: schema_error_422()},
)
@api_view(["GET"])
def get_work_order_status_history_api(request, work_order_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    history_data, messages = get_work_order_status_history(
        technician_operating=technician_operating,
        work_order_id=work_order_id
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
        "success": "Work order status history retrieved",
        "work_order_id": str(work_order_id),
        "status_history": history_data,
        "messages": messages,
    }, status=status.HTTP_200_OK)
