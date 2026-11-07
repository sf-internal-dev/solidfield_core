from backend.apps.checklist.services.checklist_service import (
    create_checklist,
    bulk_save_answers,
    remove_answer,
    list_missing_required_answers,
    list_checklists,
    get_checklist,
    submit_checklist,
    get_checklist_progress,
)
from backend.apps.checklist.services.checklist_export_service import export_checklist_answers_csv
from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.core.models.technician import Technician
from backend.apps.checklist.models import Checklist, ChecklistItemTemplate, ChecklistTemplate
from backend.apps.orders.models import WorkOrder
from backend.apps.checklist.api.serializers.checklist_serializers import ChecklistSerializer, ChecklistDetailSerializer
from backend.apps.apis.spectacular_public import TAG_CHECKLIST, schema_error_401, schema_error_422

_JSON_OBJECT = {"type": "object", "additionalProperties": True}


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistCreate",
    summary="Creates a checklist instance (optional trip via work_order)",
    request={
        "application/json": {
            "type": "object",
            "required": ["template"],
            "properties": {
                "template": {"type": "integer"},
                "work_order": {"type": "integer", "nullable": True},
                "filled_by": {"type": "integer", "nullable": True},
            },
        }
    },
    responses={201: _JSON_OBJECT, 401: schema_error_401(), 422: schema_error_422()},
)
@api_view(["POST"])
def create_checklist_api(request):
    data = request.data or {}

    template_id = data.get("template")
    work_order_id = data.get("work_order")
    filled_by_id = data.get("filled_by")

    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    pre_messages = []
    template = None
    if template_id is None:
        pre_messages.append("template_required")
    elif technician_operating is None:
        pre_messages.append("technician_operating_required")
    else:
        try:
            template = ChecklistTemplate.objects.get(
                pk=template_id,
                tenant_id=technician_operating.tenant_id,
            )
        except ChecklistTemplate.DoesNotExist:
            pre_messages.append("template_not_found")

    work_order = None
    if work_order_id is not None and technician_operating is not None:
        try:
            work_order = WorkOrder.objects.get(
                pk=work_order_id,
                tenant_id=technician_operating.tenant_id,
            )
        except WorkOrder.DoesNotExist:
            pre_messages.append("work_order_not_found")

    filled_by = None
    if filled_by_id is not None and technician_operating is not None:
        try:
            filled_by = Technician.objects.get(
                pk=filled_by_id,
                tenant_id=technician_operating.tenant_id,
            )
        except Technician.DoesNotExist:
            pre_messages.append("filled_by_not_found")

    if pre_messages:
        payloads = [get_error_payload(c) for c in pre_messages]
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
        return Response(
            {"codes": pre_messages, "correlation_id": correlation},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    checklist, messages = create_checklist(
        technician_operating=technician_operating,
        template=template,
        work_order=work_order,
        filled_by=filled_by,
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
        "success": "Checklist registered",
        "checklist_id":  str(checklist.id),
        "messages": messages,
        # maybe I'll make the register functions return a data payload
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistBulkAnswers",
    summary="Saves answers in bulk (checklist + answers list)",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "checklist": {"type": "integer"},
                "answers": {
                    "type": "array",
                    "items": {"type": "object", "additionalProperties": True},
                },
            },
        }
    },
    responses={201: _JSON_OBJECT, 422: schema_error_422()},
)
@api_view(["POST"])
def create_checklist_item_answer_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)
    answers = data.get("answers", [])  # expects a list of dicts
    checklist_id = data.get("checklist")

    checklist = None
    if checklist_id is not None:
        checklist = Checklist.objects.get(pk=checklist_id)

    possible_fields = ["answer_bool", "answer_texto", "answer_number", "answer_choice"]
    payloads = []
    for ans in answers:
        item_template = ans.get("item_template")
        note = ans.get("note") if "note" in ans else None

        # detects the value field that is present (priority follows the possible order)
        value = None
        for field in possible_fields:
            if field in ans:
                value = ans[field]
                break

        payloads.append({
            "item_template": item_template,
            "value": value,
            "note": note,
        })
    
    saved, messages = bulk_save_answers(
        technician_operating=technician_operating,
        checklist=checklist,
        payloads=payloads,
    )

    missing_after_save, list_errors = list_missing_required_answers(checklist=checklist)

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
        return Response({"codes": messages, "correlation_id": correlation, "saved_count":len(saved)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response(
        {
            "success": "Checklist answers registered",
            "saved": [str(a.id) for a in saved],
            "saved_count": len(saved),
            "messages": messages + list_errors,
            "missing_after_save": missing_after_save,
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistList",
    summary="Lists checklists with optional filters",
    parameters=[
        OpenApiParameter("technician_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("template_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("work_order_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("status", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY),
    ],
    responses={200: _JSON_OBJECT, 422: schema_error_422()},
)
@api_view(["GET"])
def list_checklists_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Get query parameters
    technician_id = request.GET.get("technician_id")
    template_id = request.GET.get("template_id")
    work_order_id = request.GET.get("work_order_id")
    status_filter = request.GET.get("status")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    # Convert string IDs to integers if provided
    technician_id = int(technician_id) if technician_id else None
    template_id = int(template_id) if template_id else None
    work_order_id = int(work_order_id) if work_order_id else None

    checklists, messages = list_checklists(
        technician_operating=technician_operating,
        technician_id=technician_id,
        template_id=template_id,
        work_order_id=work_order_id,
        status=status_filter,
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

    # Serialize checklists
    serializer = ChecklistSerializer(checklists, many=True)

    return Response({
        "success": "Checklists retrieved",
        "checklists": serializer.data,
        "count": len(checklists),
        "limit": limit,
        "offset": offset,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistGet",
    summary="Checklist detail with answers",
    responses={200: _JSON_OBJECT, 422: schema_error_422()},
)
@api_view(["GET"])
def get_checklist_api(request, checklist_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    checklist, messages = get_checklist(
        technician_operating=technician_operating,
        checklist_id=checklist_id
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

    # Serialize checklist with detailed information
    serializer = ChecklistDetailSerializer(checklist)

    return Response({
        "success": "Checklist retrieved",
        "checklist": serializer.data,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistSubmit",
    summary="Submits checklist (validates required items)",
    responses={200: _JSON_OBJECT, 422: schema_error_422()},
)
@api_view(["POST"])
def submit_checklist_api(request, checklist_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    success, messages = submit_checklist(
        technician_operating=technician_operating,
        checklist_id=checklist_id
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
        "success": "Checklist submitted successfully",
        "checklist_id": str(checklist_id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistProgress",
    summary="Progress and aggregated answers",
    responses={200: _JSON_OBJECT, 422: schema_error_422()},
)
@api_view(["GET"])
def get_checklist_progress_api(request, checklist_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    progress_data, messages = get_checklist_progress(
        technician_operating=technician_operating,
        checklist_id=checklist_id
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
        "success": "Checklist progress retrieved",
        "progress": progress_data,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistRemoveAnswer",
    summary="Removes an answer (checklist + item_template)",
    responses={200: _JSON_OBJECT, 404: schema_error_401(), 422: schema_error_422()},
)
@api_view(["DELETE"])
def remove_checklist_answer_api(request, checklist_id, item_template_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    try:
        checklist = Checklist.objects.get(id=checklist_id, template__tenant=technician_operating.tenant)
    except Checklist.DoesNotExist:
        return Response({
            "codes": ["checklist_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        item_template = ChecklistItemTemplate.objects.get(id=item_template_id, template=checklist.template)
    except ChecklistItemTemplate.DoesNotExist:
        return Response({
            "codes": ["item_template_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    success, messages = remove_answer(
        technician_operating=technician_operating,
        checklist=checklist,
        item_template=item_template
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
        "success": "Answer removed",
        "checklist_id": str(checklist.id),
        "item_template_id": str(item_template.id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=[TAG_CHECKLIST],
    operation_id="publicV1ChecklistExportCsv",
    summary="Export answers CSV for BI",
    parameters=[
        OpenApiParameter("work_order_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("service_type", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("template_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
    ],
    responses={200: OpenApiTypes.BINARY},
)
@api_view(["GET"])
def export_checklist_answers_csv_api(request):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    if technician_operating is None:
        return Response(
            {"codes": ["technician_operating_required"], "correlation_id": None},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    work_order_id = request.GET.get("work_order_id")
    service_type = request.GET.get("service_type") or None
    template_id = request.GET.get("template_id")

    try:
        wo_id = int(work_order_id) if work_order_id else None
    except (TypeError, ValueError):
        return Response(
            {"codes": ["invalid_work_order_id"], "correlation_id": None},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        tpl_id = int(template_id) if template_id else None
    except (TypeError, ValueError):
        return Response(
            {"codes": ["invalid_template_id"], "correlation_id": None},
            status=status.HTTP_400_BAD_REQUEST,
        )

    csv_text, messages = export_checklist_answers_csv(
        technician_operating=technician_operating,
        work_order_id=wo_id,
        service_type=service_type,
        template_id=tpl_id,
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]
        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None
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
        return Response(
            {"codes": messages, "correlation_id": correlation},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    response = HttpResponse("\ufeff" + csv_text, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="checklist_answers_export.csv"'
    return response