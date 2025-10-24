# Technician APIs Documentation

## Overview
This document describes the technician-related APIs implemented in the SolidField system.

## Available APIs

### 1. Register Technician
- **Endpoint**: `POST /api/register_technician_api/`
- **Description**: Creates a new technician
- **Required Permission**: `register_technician`

**Request Body:**
```json
{
    "username": "tech001",
    "social_name": "John Doe",
    "technician_permission": "L1"
}
```

**Response:**
```json
{
    "success": "Technician registered",
    "id": "123",
    "messages": []
}
```

### 2. Update Technician
- **Endpoint**: `PUT /api/update_technician_api/<technician_id>/`
- **Description**: Updates an existing technician's information
- **Required Permission**: `manage_technicians`

**Request Body:**
```json
{
    "social_name": "John Smith",
    "username": "tech001_updated",
    "technician_permission": "L2",
    "is_active": true,
    "aggroupment": 5
}
```

**Response:**
```json
{
    "success": "Technician updated",
    "id": "123",
    "messages": []
}
```

### 3. Delete Technician
- **Endpoint**: `DELETE /api/delete_technician_api/<technician_id>/`
- **Description**: Soft deletes a technician (sets is_active to false)
- **Required Permission**: `manage_technicians`

**Response:**
```json
{
    "success": "Technician deleted",
    "messages": []
}
```

### 4. Delegate Permissions
- **Endpoint**: `POST /api/delegate_permissions_api/`
- **Description**: Delegates permissions to another technician
- **Required Permission**: `delegate_temporary_permissions` or `delegate_permission_level`

**Request Body (Permanent Delegation):**
```json
{
    "delegation_type": "permanent",
    "from_user": 123,
    "to_user": 456,
    "level": "L2"
}
```

**Request Body (Temporary Delegation):**
```json
{
    "delegation_type": "temporary",
    "from_user": 123,
    "to_user": 456,
    "actions": ["submit_checklist", "upload_photos"],
    "valid_from": "2024-01-01T00:00:00Z",
    "valid_until": "2024-01-31T23:59:59Z"
}
```

**Response:**
```json
{
    "success": "Permissions delegated successfully (permanent)",
    "messages": []
}
```

### 5. Get Technician Permissions
- **Endpoint**: `GET /api/get_technician_permissions_api/<technician_id>/`
- **Description**: Retrieves a technician's effective permissions and delegations
- **Required Permission**: `manage_technicians`

**Response:**
```json
{
    "technician": {
        "id": 123,
        "username": "tech001",
        "social_name": "John Doe",
        "permission_level": "L2"
    },
    "effective_permissions": [
        "submit_checklist",
        "upload_photos",
        "view_assigned_work_orders"
    ],
    "outgoing_delegations": [
        {
            "id": 1,
            "to_user": {
                "id": 456,
                "username": "tech002",
                "social_name": "Jane Smith"
            },
            "actions": ["submit_checklist"],
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_until": "2024-01-31T23:59:59Z",
            "is_active": true
        }
    ],
    "incoming_delegations": []
}
```

### 6. Revoke Delegation
- **Endpoint**: `DELETE /api/revoke_delegation_api/<delegation_id>/`
- **Description**: Revokes a temporary delegation created by the technician
- **Required Permission**: Implicit (can only revoke own delegations)

**URL Parameters:**
- `delegation_id`: ID of the delegation to revoke

**Response:**
```json
{
    "success": "Delegation revoked",
    "delegation_id": "1",
    "from_user_id": "123",
    "to_user_id": "456",
    "messages": []
}
```

**Error Responses:**
- `404 Not Found`: If delegation not found
- `403 Forbidden`: If trying to revoke someone else's delegation

## Error Handling

All APIs return consistent error responses:

**Error Response:**
```json
{
    "codes": ["invalid_username", "technician_not_found"],
    "correlation_id": "abc123"
}
```

**Common Error Codes:**
- `invalid_social_name`: Invalid social name format
- `invalid_username`: Invalid username format
- `invalid_technician_permission`: Invalid permission level
- `technician_not_found`: Technician not found
- `cannot_delete_self`: Cannot delete own account
- `delegator_not_manager`: Only managers can delegate permissions
- `tried_to_delegate_to_itself`: Cannot delegate to self
- `delegation_not_found`: Delegation not found
- `cannot_revoke_others_delegation`: Can only revoke own delegations

## Permission Levels

- **L1**: Field Level - Basic execution permissions
- **L2**: Local Control - Supervision permissions
- **L3**: Operational Management - Full control permissions

## Notes

- All APIs require proper authentication
- All operations are scoped to the technician's tenant
- Soft deletion is used (is_active = false) instead of hard deletion
- Permission delegation supports both permanent and temporary types
- All timestamps are in ISO 8601 format
