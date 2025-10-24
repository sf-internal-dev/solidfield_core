# Checklist APIs Documentation

## Overview
This document describes the checklist-related APIs implemented in the SolidField system.

## Available APIs

### 1. Create Checklist
- **Endpoint**: `POST /api/create_checklist_api/`
- **Description**: Creates a new checklist instance
- **Required Permission**: `submit_checklist`

**Request Body:**
```json
{
    "template": 123,
    "work_order": 456
}
```

**Response:**
```json
{
    "success": "Checklist registered",
    "checklist_id": "789",
    "messages": []
}
```

### 2. Create Checklist Item Answer
- **Endpoint**: `POST /api/create_checklist_item_answer_api/`
- **Description**: Saves or updates checklist item answers
- **Required Permission**: `save_answer`

**Request Body:**
```json
{
    "checklist": 789,
    "answers": [
        {
            "item_template": 1,
            "answer_bool": true,
            "note": "All systems operational"
        },
        {
            "item_template": 2,
            "answer_texto": "Equipment is in good condition",
            "note": "Regular maintenance completed"
        },
        {
            "item_template": 3,
            "answer_number": 25.5,
            "note": "Temperature reading"
        },
        {
            "item_template": 4,
            "answer_choice": "excellent",
            "note": "Customer satisfaction"
        }
    ]
}
```

**Response:**
```json
{
    "success": "Checklist answers registered",
    "saved": ["101", "102", "103", "104"],
    "saved_count": 4,
    "messages": [],
    "missing_after_save": []
}
```

### 3. List Checklists
- **Endpoint**: `GET /api/list_checklists_api/`
- **Description**: Lists checklists with optional filtering
- **Required Permission**: `view_checklists`

**Query Parameters:**
- `technician_id` (optional): Filter by technician
- `template_id` (optional): Filter by template
- `work_order_id` (optional): Filter by work order
- `status` (optional): Filter by status
- `limit` (optional, default: 50): Number of results per page
- `offset` (optional, default: 0): Pagination offset

**Example Request:**
```
GET /api/list_checklists_api/?technician_id=123&status=draft&limit=20&offset=0
```

**Response:**
```json
{
    "success": "Checklists retrieved",
    "checklists": [
        {
            "id": 789,
            "template": {
                "id": 123,
                "name": "Equipment Inspection",
                "service_type": "maintenance",
                "version": 1,
                "is_global": false,
                "tenant": {
                    "id": 1,
                    "name": "SolidField Corp"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "filled_by": {
                "id": 456,
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
            "work_order_id": 456,
            "work_order_identifier": "SOLI0001",
            "status": "draft",
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

### 4. Get Checklist
- **Endpoint**: `GET /api/get_checklist_api/<checklist_id>/`
- **Description**: Retrieves detailed information about a specific checklist
- **Required Permission**: `view_checklists`

**Response:**
```json
{
    "success": "Checklist retrieved",
    "checklist": {
        "id": 789,
        "template": {
            "id": 123,
            "name": "Equipment Inspection",
            "service_type": "maintenance",
            "version": 1,
            "is_global": false,
            "tenant": {
                "id": 1,
                "name": "SolidField Corp"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "filled_by": {
            "id": 456,
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
        "work_order_id": 456,
        "work_order_identifier": "SOLI0001",
        "status": "draft",
        "answers": [
            {
                "id": 101,
                "item_template_id": 1,
                "question": "Is the equipment functioning properly?",
                "answer_type": "bool",
                "required": true,
                "answer_bool": true,
                "answer_texto": null,
                "answer_number": null,
                "answer_choice": null,
                "note": "All systems operational",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "messages": []
}
```

### 5. Submit Checklist
- **Endpoint**: `POST /api/submit_checklist_api/<checklist_id>/`
- **Description**: Submits a checklist for final review/completion
- **Required Permission**: `submit_checklist`

**Response:**
```json
{
    "success": "Checklist submitted successfully",
    "checklist_id": "789",
    "messages": []
}
```

### 6. Get Checklist Progress
- **Endpoint**: `GET /api/get_checklist_progress_api/<checklist_id>/`
- **Description**: Retrieves progress statistics for a checklist
- **Required Permission**: `view_checklists`

**Response:**
```json
{
    "success": "Checklist progress retrieved",
    "progress": {
        "checklist_id": 789,
        "template_name": "Equipment Inspection",
        "status": "draft",
        "total_items": 10,
        "required_items": 8,
        "answered_items": 6,
        "missing_required_items": 2,
        "progress_percentage": 60.0,
        "required_progress_percentage": 75.0,
        "is_complete": false,
        "can_submit": false,
        "answers": [
            {
                "id": 101,
                "item_template_id": 1,
                "question": "Is the equipment functioning properly?",
                "answer_type": "bool",
                "required": true,
                "answer_bool": true,
                "answer_texto": null,
                "answer_number": null,
                "answer_choice": null,
                "note": "All systems operational",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ],
        "missing_required_item_ids": [3, 7]
    },
    "messages": []
}
```

## Error Handling

All APIs return consistent error responses:

**Error Response:**
```json
{
    "codes": ["checklist_not_found", "missing_required_answers"],
    "correlation_id": "abc123"
}
```

**Common Error Codes:**
- `checklist_not_found`: Checklist not found
- `checklist_already_submitted`: Checklist already submitted
- `missing_required_answers`: Some required answers are missing
- `item_template_not_found`: Checklist item template not found
- `required_value_missing`: A required value is missing
- `choice_not_in_options`: The selected option is not valid

## Answer Types

The system supports different answer types:

### Boolean (`answer_bool`)
- `true` or `false`
- Used for yes/no questions

### Text (`answer_texto`)
- String values
- Used for open-ended questions

### Number (`answer_number`)
- Numeric values
- Used for measurements, counts, etc.

### Choice (`answer_choice`)
- Predefined options
- Must match one of the template's choice options

## Checklist Status

- `draft`: Checklist is being filled out
- `submitted`: Checklist has been submitted for review
- `approved`: Checklist has been approved
- `rejected`: Checklist has been rejected

## Progress Calculation

- **Total Progress**: Percentage of all items answered
- **Required Progress**: Percentage of required items answered
- **Can Submit**: True if all required items are answered
- **Is Complete**: True if all required items are answered and checklist is ready

## Notes

- All APIs require proper authentication
- Checklist operations are scoped to the technician's tenant
- All timestamps are in ISO 8601 format
- Pagination is supported for list operations
- Progress calculation includes detailed statistics
- Answer validation ensures data integrity
