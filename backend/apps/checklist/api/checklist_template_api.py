from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.checklist.services.checklist_template_service import (next_order_for_template, remove_aggroupment_from_template, create_checklist_template, 
add_item_to_checklist_template, delegate_checklist_template_to_aggroupment, update_checklist_template_version,)
from backend.apps.checklist.models import ChecklistTemplate
from backend.apps.orders.models import WorkOrder
from backend.apps.core.models import TechniciansAggroupment

@api_view(["POST"])
def create_checklist_template_api(request):
    data = request.data or {}
    
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    name = data.get("name")
    service_type = data.get("service_type")

    checklist_template, messages = create_checklist_template(
        technician_operating=technician_operating,
        name = name,
        service_type = service_type,
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

    
@api_view(["POST"])
def create_checklist_item_template_api(request):
    data = request.data or {}
    template_id = data.get("template")

    template = None
    if template_id is not None:
        template = ChecklistTemplate.objects.get(pk=template_id)

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


@api_view(["GET"])
def get_next_order_for_template_api(request, template_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    try:
        template = ChecklistTemplate.objects.get(id=template_id, tenant=technician_operating.tenant)
    except ChecklistTemplate.DoesNotExist:
        return Response({
            "codes": ["template_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    next_order = next_order_for_template(template)

    return Response({
        "success": "Next order retrieved",
        "template_id": template_id,
        "next_order": next_order,
        "messages": []
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
def delegate_checklist_template_to_aggroupment_api(request, template_id):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    aggroupment_id = data.get("aggroupment_id")

    try:
        template = ChecklistTemplate.objects.get(id=template_id, tenant=technician_operating.tenant)
    except ChecklistTemplate.DoesNotExist:
        return Response({
            "codes": ["template_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        aggroupment = TechniciansAggroupment.objects.get(id=aggroupment_id, tenant=technician_operating.tenant)
    except TechniciansAggroupment.DoesNotExist:
        return Response({
            "codes": ["aggroupment_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    updated_template, messages = delegate_checklist_template_to_aggroupment(
        technician_operating=technician_operating,
        template=template,
        aggroupment=aggroupment
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
        "success": "Template delegated to aggroupment",
        "template_id": str(template.id),
        "aggroupment_id": str(aggroupment.id),
        "is_global": updated_template.is_global,
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def remove_aggroupment_from_template_api(request, template_id, aggroupment_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    try:
        template = ChecklistTemplate.objects.get(id=template_id, tenant=technician_operating.tenant)
    except ChecklistTemplate.DoesNotExist:
        return Response({
            "codes": ["template_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        aggroupment = TechniciansAggroupment.objects.get(id=aggroupment_id, tenant=technician_operating.tenant)
    except TechniciansAggroupment.DoesNotExist:
        return Response({
            "codes": ["aggroupment_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    updated_template, messages = remove_aggroupment_from_template(
        technician_operating=technician_operating,
        template=template,
        aggroupment=aggroupment
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
        "success": "Aggroupment removed from template",
        "template_id": str(template.id),
        "aggroupment_id": str(aggroupment.id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
def update_checklist_template_version_api(request, template_id):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    try:
        template = ChecklistTemplate.objects.get(id=template_id, tenant=technician_operating.tenant)
    except ChecklistTemplate.DoesNotExist:
        return Response({
            "codes": ["template_not_found"],
            "correlation_id": None
        }, status=status.HTTP_404_NOT_FOUND)

    # Extract parameters
    orders_to_remove = data.get("orders_to_remove", [])
    items_to_add = data.get("items_to_add", [])
    copy_aggroupments = data.get("copy_aggroupments", True)
    deactivate_previous = data.get("deactivate_previous", True)

    new_template, messages = update_checklist_template_version(
        technician_operating=technician_operating,
        template=template,
        orders_to_remove=orders_to_remove,
        items_to_add=items_to_add,
        copy_aggroupments=copy_aggroupments,
        deactivate_previous=deactivate_previous
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
        "success": "Template version updated",
        "original_template_id": str(template.id),
        "new_template_id": str(new_template.id),
        "new_version": new_template.version,
        "is_global": new_template.is_global,
        "is_active": new_template.is_active,
        "messages": messages,
    }, status=status.HTTP_201_CREATED)
