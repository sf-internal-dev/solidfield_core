from backend.apps.checklist.services.checklist_service import create_checklist, save_answer, bulk_save_answers, remove_answer, list_missing_required_answers
from backend.apps.checklist.services.checklist_template_service import (next_order_for_template, remove_aggroupment_from_template, create_checklist_template, 
add_item_to_checklist_template, delegate_checklist_template_to_aggroupment, update_checklist_template_version,)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.checklist.models import ChecklistTemplate, Checklist, ChecklistItemAnswer, ChecklistItemTemplate
from backend.apps.core.models import Technician, TechniciansAggroupment
from typing import Tuple, List, Optional
from backend.apps.core.services.technician_permission_service import has_permission

@api_view(["POST"])
def create_checklist_template_api(request):
    data = request.data or {}
    
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    name = data.get("name")
    service_type = data.get("service_type")
    aggroupment = data.get("aggroupment")

    checklist_template, messages = create_checklist_template(
        technician_operating=technician_operating,
        name = name,
        service_type = service_type,
        aggroupment = aggroupment if aggroupment else None,
        is_global= False if aggroupment else True
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
        "success": "Checklist Template registered",
        "checklist_template_id":  str(checklist_template.id),
        "messages": messages,
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)

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
    

def create_checklist_item_template_api(request):
    data = request.data or {}
    template = data.get("template")
    order = data.get("order")
    question = data.get("question")
    answer_type = data.get("answer_type")
    is_required = data.get("is_required")
    choice_options = data.get("choice_options")

    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    checklist_item_template, messages = add_item_to_checklist_template(
        technician_operating = technician_operating,
        template = template,
        order = order,
        question = question,
        answer_type = answer_type,
        is_required = is_required,
        choice_options = choice_options if choice_options else None
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
        "success": "Checklist Item Template registered",
        "checklist_item_template_id":  str(checklist_item_template.id),
        "messages": messages,
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)

def create_checklist_item_answer_api(request):
    data = request.data or {}
    checklist = data.get("checklist")
    item_template = data.get("item_template")
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)


    possible_fields = ["answer_bool", "answer_texto", "answer_number", "answer_choice"]

    for field in possible_fields:
        if field in data:
            answer_value = data[field]
            break
    
    checklist_item_answer, messages = save_answer(
        technician_operating = technician_operating,
        checklist = checklist,
        item_template = item_template,
        value=answer_value
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
        "success": "Checklist Item Answer registered",
        "checklist_item_answer_id":  str(checklist_item_answer.id),
        "messages": messages,
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)
