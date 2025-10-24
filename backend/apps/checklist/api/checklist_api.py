from backend.apps.checklist.services.checklist_service import create_checklist, bulk_save_answers, remove_answer, list_missing_required_answers, list_checklists, get_checklist, submit_checklist, get_checklist_progress
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.core.services.technician_permission_service import has_permission
from backend.apps.checklist.models import Checklist, ChecklistTemplate
from backend.apps.orders.models import WorkOrder
from backend.apps.checklist.api.serializers.checklist_serializers import ChecklistSerializer, ChecklistDetailSerializer

@api_view(["POST"])
def create_checklist_api(request):
    data = request.data or {}

    template_id = data.get("template")

    template = None
    if template_id is not None:
        template = ChecklistTemplate.objects.get(pk=template_id)

    work_order_id = data.get("work_order")

    work_order = None
    if work_order_id is not None:
        work_order = WorkOrder.objects.get(pk=work_order_id)

    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)


    checklist, messages = create_checklist(
        technician_operating=technician_operating,
        template = template,
        work_order = work_order,
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
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def create_checklist_item_answer_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)
    answers = data.get("answers", [])  # espera lista de dicts
    checklist_id = data.get("checklist")

    checklist = None
    if checklist_id is not None:
        checklist = Checklist.objects.get(pk=checklist_id)

    possible_fields = ["answer_bool", "answer_texto", "answer_number", "answer_choice"]
    payloads = []
    for ans in answers:
        item_template = ans.get("item_template")
        note = ans.get("note") if "note" in ans else None

        # detecta o campo de valor presente (prioridade na ordem possível)
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
    
    saved, messages = bulk_save_answers(checklist=checklist, payloads=payloads)

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