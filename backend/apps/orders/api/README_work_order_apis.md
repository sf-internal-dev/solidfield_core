# Work Order APIs Documentation

## Overview
This document describes the work order-related APIs implemented in the SolidField system.

## Available APIs

### 1. Create Work Order
- **Endpoint**: `POST /api/create_work_order_api/`
- **Description**: Creates a new work order with unique identifier
- **Required Permission**: Manager account

**Request Body:**
```json
{
    "company": 123,
    "title": "Equipment Maintenance",
    "description": "Routine maintenance of production equipment",
    "priority": "medium",
    "location": "Building A, Floor 2",
    "due_date": "2024-02-15T10:00:00Z"
}
```

**Response:**
```json
{
    "success": "Work Order registered",
    "work_order_id": "789",
    "messages": []
}
```

### 2. Create Work Order Download Link
- **Endpoint**: `POST /api/create_work_order_download_link_api/`
- **Description**: Creates a download link for work order documents
- **Required Permission**: Manager account

**Request Body:**
```json
{
    "work_order": 789,
    "purpose": "general",
    "days": 7
}
```

**Response:**
```json
{
    "success": "Work Order Download Link registered",
    "work_order_download_link_id": "101",
    "messages": []
}
```

### 3. List Work Orders
- **Endpoint**: `GET /api/list_work_orders_api/`
- **Description**: Lists work orders with optional filtering
- **Required Permission**: `view_work_orders`

**Query Parameters:**
- `technician_id` (optional): Filter by assigned technician
- `status` (optional): Filter by status
- `tenant_id` (optional): Filter by tenant
- `limit` (optional, default: 50): Number of results per page
- `offset` (optional, default: 0): Pagination offset

**Example Request:**
```
GET /api/list_work_orders_api/?technician_id=123&status=assigned&limit=20&offset=0
```

**Response:**
```json
{
    "success": "Work orders retrieved",
    "work_orders": [
        {
            "id": 789,
            "identifier": "SOLI0001",
            "title": "Equipment Maintenance",
            "description": "Routine maintenance of production equipment",
            "status": "assigned",
            "priority": "medium",
            "tenant": {
                "id": 1,
                "name": "SolidField Corp"
            },
            "assigned_to": {
                "id": 123,
                "username": "tech001",
                "social_name": "John Doe",
                "technician_permission": "L1",
                "aggroupment": {
                    "id": 1,
                    "tag": "Field Team",
                    "allowed_to_operate": true,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "created_by": {
                "id": 456,
                "username": "manager001",
                "social_name": "Jane Manager",
                "technician_permission": "L3",
                "aggroupment": {
                    "id": 2,
                    "tag": "Management",
                    "allowed_to_operate": true,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "due_date": "2024-02-15T10:00:00Z",
            "location": "Building A, Floor 2",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ],
    "count": 1,
    "limit": 20,
    "offset": 0,
    "messages": []
}
```

### 4. Get Work Order
- **Endpoint**: `GET /api/get_work_order_api/<work_order_id>/`
- **Description**: Retrieves detailed information about a specific work order
- **Required Permission**: `view_work_orders`

**Response:**
```json
{
    "success": "Work order retrieved",
    "work_order": {
        "id": 789,
        "identifier": "SOLI0001",
        "title": "Equipment Maintenance",
        "description": "Routine maintenance of production equipment",
        "status": "assigned",
        "priority": "medium",
        "tenant": {
            "id": 1,
            "name": "SolidField Corp"
        },
        "assigned_to": {
            "id": 123,
            "username": "tech001",
            "social_name": "John Doe",
            "technician_permission": "L1",
            "aggroupment": {
                "id": 1,
                "tag": "Field Team",
                "allowed_to_operate": true,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "created_by": {
            "id": 456,
            "username": "manager001",
            "social_name": "Jane Manager",
            "technician_permission": "L3",
            "aggroupment": {
                "id": 2,
                "tag": "Management",
                "allowed_to_operate": true,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "due_date": "2024-02-15T10:00:00Z",
        "location": "Building A, Floor 2",
        "notes": "Special attention to hydraulic systems",
        "status_history": [
            {
                "id": 1,
                "status": "assigned",
                "changed_by": {
                    "id": 456,
                    "username": "manager001",
                    "social_name": "Jane Manager"
                },
                "notes": "Work order assigned to John Doe",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ],
        "download_links": [
            {
                "id": 101,
                "key": "abc123def456",
                "purpose": "general",
                "expires_at": "2024-01-08T10:00:00Z",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
    },
    "messages": []
}
```

### 5. Update Work Order
- **Endpoint**: `PUT /api/update_work_order_api/<work_order_id>/`
- **Description**: Updates an existing work order's information
- **Required Permission**: `manage_work_orders`

**Request Body:**
```json
{
    "title": "Updated Equipment Maintenance",
    "description": "Updated description with more details",
    "priority": "high",
    "status": "in_progress",
    "assigned_to": 123,
    "due_date": "2024-02-20T10:00:00Z",
    "location": "Building A, Floor 2, Room 201",
    "notes": "Updated notes with additional information"
}
```

**Response:**
```json
{
    "success": "Work order updated",
    "work_order_id": "789",
    "messages": []
}
```

### 6. Assign Work Order
- **Endpoint**: `POST /api/assign_work_order_api/<work_order_id>/`
- **Description**: Assigns a work order to a technician
- **Required Permission**: `assign_work_orders`

**Request Body:**
```json
{
    "technician_id": 123
}
```

**Response:**
```json
{
    "success": "Work order assigned successfully",
    "work_order_id": "789",
    "technician_id": "123",
    "messages": []
}
```

### 7. Get Work Order Status History
- **Endpoint**: `GET /api/get_work_order_status_history_api/<work_order_id>/`
- **Description**: Retrieves the status change history for a work order
- **Required Permission**: `view_work_orders`

**Response:**
```json
{
    "success": "Work order status history retrieved",
    "work_order_id": "789",
    "status_history": [
        {
            "id": 3,
            "status": "in_progress",
            "changed_by": {
                "id": 123,
                "username": "tech001",
                "social_name": "John Doe"
            },
            "notes": "Started working on the equipment",
            "created_at": "2024-01-02T09:00:00Z"
        },
        {
            "id": 2,
            "status": "assigned",
            "changed_by": {
                "id": 456,
                "username": "manager001",
                "social_name": "Jane Manager"
            },
            "notes": "Work order assigned to John Doe",
            "created_at": "2024-01-01T10:00:00Z"
        },
        {
            "id": 1,
            "status": "pending",
            "changed_by": {
                "id": 456,
                "username": "manager001",
                "social_name": "Jane Manager"
            },
            "notes": "Work order created",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ],
    "messages": []
}
```

## Error Handling

All APIs return consistent error responses:

**Error Response:**
```json
{
    "codes": ["work_order_not_found", "invalid_priority"],
    "correlation_id": "abc123"
}
```

**Common Error Codes:**
- `work_order_not_found`: Work order not found
- `technician_not_found`: Technician not found
- `invalid_priority`: Invalid priority value
- `invalid_status`: Invalid status value

## Work Order Fields

### Basic Information
- `id`: Unique identifier
- `identifier`: Human-readable identifier (e.g., "SOLI0001")
- `title`: Work order title
- `description`: Detailed description
- `status`: Current status
- `priority`: Priority level
- `location`: Work location
- `due_date`: Due date and time
- `notes`: Additional notes

### Relationships
- `tenant`: Associated tenant/company
- `assigned_to`: Assigned technician
- `created_by`: Creator of the work order

### Status Values
- `pending`: Work order created but not assigned
- `assigned`: Assigned to a technician
- `in_progress`: Currently being worked on
- `completed`: Work completed
- `cancelled`: Work order cancelled

### Priority Values
- `low`: Low priority
- `medium`: Medium priority
- `high`: High priority
- `urgent`: Urgent priority

## Status History

The status history tracks all changes to a work order's status:
- `id`: History entry ID
- `status`: Status at the time of change
- `changed_by`: Technician who made the change
- `notes`: Additional notes about the change
- `created_at`: Timestamp of the change

## Download Links

Work order download links provide access to related documents:
- `id`: Link ID
- `key`: Unique access key
- `purpose`: Purpose of the link
- `expires_at`: Expiration timestamp
- `created_at`: Creation timestamp

## Notes

- All APIs require proper authentication
- Work order operations are scoped to the technician's tenant
- All timestamps are in ISO 8601 format
- Pagination is supported for list operations
- Status changes are automatically logged
- Assignment changes are logged for audit purposes
