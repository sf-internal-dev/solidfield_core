from backend.apps.checklist.services.checklist_service import create_checklist, bulk_save_answers, remove_answer, list_missing_required_answers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.core.services.technician_permission_service import has_permission
from backend.apps.checklist.models import Checklist

@api_view(["POST"])
def create_checklist_api(request):
    data = request.data or {}
    template = data.get("template")
    work_order = data.get("work_order")
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