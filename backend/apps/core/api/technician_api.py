import hashlib
from backend.apps.core.services.technician_permission_service import delegate_permission_level, create_temporary_delegation, has_permission, list_effective_permissions, revoke_delegation, list_outgoing_delegations, list_incoming_delegations
from backend.apps.core.services.technician_registration_service import register_technician, update_technician, delete_technician
from backend.common.schemas.error_messages_schema import get_error_payload
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.apps.core.models import Technician, TemporaryDelegation
from django.utils import timezone


@api_view(["POST"])
def register_technician_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)

    username = data.get("username")
    social_name = data.get("social_name")
    technician_permission = data.get("technician_permission")

    technician, messages = register_technician(
            technician_operating=technician_operating,
            username=username,
            social_name=social_name,
            technician_permission=technician_permission,
    )
    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician is not None and getattr(technician, "tenant", None) is not None:
            tenant_id = getattr(technician.tenant, "id", None)
        elif technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

        manager_account_operating = getattr(request.user, "id", None)

        correlation = publish_ui_messages(
            payloads=payloads,
            technician_operating_id=technician_operating,
            recipient_technician_id=technician_operating,
            manager_account_operating_id=manager_account_operating,
            recipient_session_id=session_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Technician registered",
        "id": str(technician.id),
        "messages": messages,
    }, status=status.HTTP_201_CREATED)


@api_view(["PUT"])
def update_technician_api(request, technician_id):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    # Extract update data
    update_data = {}
    if "social_name" in data:
        update_data["social_name"] = data["social_name"]
    if "username" in data:
        update_data["username"] = data["username"]
    if "technician_permission" in data:
        update_data["technician_permission"] = data["technician_permission"]
    if "is_active" in data:
        update_data["is_active"] = data["is_active"]
    if "aggroupment" in data:
        update_data["aggroupment"] = data["aggroupment"]

    technician, messages = update_technician(
        technician_operating=technician_operating,
        technician_id=technician_id,
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
            payloads=payloads,
            technician_operating_id=technician_operating,
            recipient_technician_id=technician_operating,
            manager_account_operating_id=manager_account_operating,
            recipient_session_id=session_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Technician updated",
        "id": str(technician.id),
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_technician_api(request, technician_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    success, messages = delete_technician(
        technician_operating=technician_operating,
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
            payloads=payloads,
            technician_operating_id=technician_operating,
            recipient_technician_id=technician_operating,
            manager_account_operating_id=manager_account_operating,
            recipient_session_id=session_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Technician deleted",
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
def delegate_permissions_api(request):
    data = request.data or {}
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    delegation_type = data.get("delegation_type")  # "permanent" or "temporary"
    from_user_id = data.get("from_user")
    to_user_id = data.get("to_user")
    actions = data.get("actions", [])
    valid_from = data.get("valid_from")
    valid_until = data.get("valid_until")

    messages = []

    try:
        from_user = Technician.objects.get(id=from_user_id, tenant=technician_operating.tenant)
        to_user = Technician.objects.get(id=to_user_id, tenant=technician_operating.tenant)
    except Technician.DoesNotExist:
        return Response({"error": "Technician not found"}, status=status.HTTP_404_NOT_FOUND)

    if delegation_type == "permanent":
        # Permanent permission level delegation
        level = data.get("level")
        success, messages = delegate_permission_level(
            delegator=technician_operating,
            delegate=to_user,
            level=level
        )
    elif delegation_type == "temporary":
        # Temporary action delegation
        if not valid_from or not valid_until:
            return Response({"error": "valid_from and valid_until are required for temporary delegation"}, status=status.HTTP_400_BAD_REQUEST)
        
        valid_from_dt = timezone.datetime.fromisoformat(valid_from.replace('Z', '+00:00'))
        valid_until_dt = timezone.datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
        
        delegation, messages = create_temporary_delegation(
            technician_operating=technician_operating,
            from_user=from_user,
            to_user=to_user,
            actions=actions,
            valid_from=valid_from_dt,
            valid_until=valid_until_dt
        )
        success = delegation is not None
    else:
        return Response({"error": "Invalid delegation_type. Must be 'permanent' or 'temporary'"}, status=status.HTTP_400_BAD_REQUEST)

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
            payloads=payloads,
            technician_operating_id=technician_operating,
            recipient_technician_id=technician_operating,
            manager_account_operating_id=manager_account_operating,
            recipient_session_id=session_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            source="django_api",
        )

        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": f"Permissions delegated successfully ({delegation_type})",
        "messages": messages,
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_technician_permissions_api(request, technician_id):
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    try:
        technician = Technician.objects.get(id=technician_id, tenant=technician_operating.tenant)
    except Technician.DoesNotExist:
        return Response({"error": "Technician not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get effective permissions
    effective_permissions = list_effective_permissions(technician)
    
    # Get outgoing delegations (delegations given by this technician)
    outgoing_delegations = list_outgoing_delegations(technician)
    outgoing_data = []
    for delegation in outgoing_delegations:
        actions = list(delegation.actions.values_list('action', flat=True))
        outgoing_data.append({
            "id": delegation.id,
            "to_user": {
                "id": delegation.to_user.id,
                "username": delegation.to_user.username,
                "social_name": delegation.to_user.social_name
            },
            "actions": actions,
            "valid_from": delegation.valid_from.isoformat(),
            "valid_until": delegation.valid_until.isoformat(),
            "is_active": delegation.is_active()
        })

    # Get incoming delegations (delegations received by this technician)
    incoming_delegations = list_incoming_delegations(technician)
    incoming_data = []
    for delegation in incoming_delegations:
        actions = list(delegation.actions.values_list('action', flat=True))
        incoming_data.append({
            "id": delegation.id,
            "from_user": {
                "id": delegation.from_user.id,
                "username": delegation.from_user.username,
                "social_name": delegation.from_user.social_name
            },
            "actions": actions,
            "valid_from": delegation.valid_from.isoformat(),
            "valid_until": delegation.valid_until.isoformat(),
            "is_active": delegation.is_active()
        })

    return Response({
        "technician": {
            "id": technician.id,
            "username": technician.username,
            "social_name": technician.social_name,
            "permission_level": technician.technician_permission
        },
        "effective_permissions": effective_permissions,
        "outgoing_delegations": outgoing_data,
        "incoming_delegations": incoming_data
    }, status=status.HTTP_200_OK)
