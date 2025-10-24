# Tenant APIs Documentation

## Overview
This document describes the tenant-related APIs implemented in the SolidField system.

## Available APIs

### 1. Register Tenant
- **Endpoint**: `POST /api/register_tenant_api/`
- **Description**: Creates a new tenant (company)
- **Required Permission**: Manager account

**Request Body:**
```json
{
    "name": "SolidField Corp",
    "slug": "solidfield-corp",
    "tenant_code": "SOLI",
    "primary_contact_name": "John Doe",
    "primary_contact_email": "john@solidfield.com",
    "primary_contact_phone": "+1234567890",
    "billing_account_id": "billing_123",
    "owner": 1,
    "country": "US",
    "locale": "en-US",
    "timezone": "America/New_York"
}
```

**Response:**
```json
{
    "success": "Tenant registered",
    "id": "123",
    "messages": []
}
```

### 2. Register Tenant Branding
- **Endpoint**: `POST /api/register_tenant_branding_api/`
- **Description**: Sets branding information for a tenant
- **Required Permission**: Manager account

**Request Body:**
```json
{
    "tenant": 123,
    "logo": "base64_encoded_image_or_file",
    "color_primary": "#FF5733"
}
```

**Response:**
```json
{
    "success": "Tenant branding registered",
    "id": "123",
    "messages": []
}
```

### 3. Update Tenant
- **Endpoint**: `PUT /api/update_tenant_api/<tenant_id>/`
- **Description**: Updates an existing tenant's information
- **Required Permission**: Manager account

**Request Body:**
```json
{
    "name": "SolidField Corporation",
    "slug": "solidfield-corporation",
    "primary_contact_name": "Jane Smith",
    "primary_contact_email": "jane@solidfield.com",
    "primary_contact_phone": "+1987654321",
    "billing_account_id": "billing_456",
    "country": "CA",
    "locale": "en-CA",
    "timezone": "America/Toronto",
    "color_primary": "#3366FF",
    "logo": "new_logo_file",
    "is_active": true
}
```

**Response:**
```json
{
    "success": "Tenant updated",
    "id": "123",
    "messages": []
}
```

### 4. Get Tenant Workflow
- **Endpoint**: `GET /api/get_tenant_workflow_api/<tenant_id>/`
- **Description**: Retrieves the current workflow configuration for a tenant
- **Required Permission**: Manager account

**Response:**
```json
{
    "success": "Tenant workflow retrieved",
    "workflow": {
        "id": 1,
        "name": "Custom Workflow",
        "workflow_json": {
            "states": [
                {
                    "id": "pending",
                    "label": "Pending",
                    "is_terminal": false
                },
                {
                    "id": "in_progress",
                    "label": "In Progress",
                    "is_terminal": false
                },
                {
                    "id": "completed",
                    "label": "Completed",
                    "is_terminal": true
                }
            ],
            "transitions": [
                {
                    "from": "pending",
                    "to": "in_progress"
                },
                {
                    "from": "in_progress",
                    "to": "completed"
                }
            ]
        }
    },
    "messages": []
}
```

### 5. Update Tenant Workflow
- **Endpoint**: `PUT /api/update_tenant_workflow_api/<tenant_id>/`
- **Description**: Updates the workflow configuration for a tenant
- **Required Permission**: Manager account

**Request Body:**
```json
{
    "workflow": {
        "name": "Updated Custom Workflow",
        "workflow_json": {
            "states": [
                {
                    "id": "new",
                    "label": "New",
                    "is_terminal": false
                },
                {
                    "id": "assigned",
                    "label": "Assigned",
                    "is_terminal": false
                },
                {
                    "id": "in_progress",
                    "label": "In Progress",
                    "is_terminal": false
                },
                {
                    "id": "review",
                    "label": "Under Review",
                    "is_terminal": false
                },
                {
                    "id": "completed",
                    "label": "Completed",
                    "is_terminal": true
                },
                {
                    "id": "cancelled",
                    "label": "Cancelled",
                    "is_terminal": true
                }
            ],
            "transitions": [
                {
                    "from": "new",
                    "to": "assigned"
                },
                {
                    "from": "assigned",
                    "to": "in_progress"
                },
                {
                    "from": "in_progress",
                    "to": "review"
                },
                {
                    "from": "review",
                    "to": "completed"
                },
                {
                    "from": "review",
                    "to": "cancelled"
                }
            ]
        }
    }
}
```

**Response:**
```json
{
    "success": "Tenant workflow updated",
    "messages": []
}
```

## Error Handling

All APIs return consistent error responses:

**Error Response:**
```json
{
    "codes": ["invalid_tenant_name", "slug_already_exists"],
    "correlation_id": "abc123"
}
```

**Common Error Codes:**
- `invalid_tenant_name`: Invalid tenant name format
- `invalid_slug_format`: Invalid slug format
- `slug_already_exists`: Slug is already in use
- `invalid_email`: Invalid email format
- `invalid_phone_number`: Invalid phone number format
- `invalid_hex_color`: Invalid color format
- `tenant_not_found`: Tenant not found

## Tenant Fields

### Basic Information
- `name`: Company name
- `slug`: URL-friendly identifier
- `tenant_code`: Short code for the tenant
- `is_active`: Whether the tenant is active

### Contact Information
- `primary_contact_name`: Main contact person
- `primary_contact_email`: Contact email
- `primary_contact_phone`: Contact phone

### Localization
- `country`: Country code
- `locale`: Locale setting (e.g., "en-US")
- `timezone`: Timezone (e.g., "America/New_York")

### Branding
- `color_primary`: Primary brand color (hex)
- `logo`: Company logo file

### Billing
- `billing_account_id`: External billing system ID

## Workflow Configuration

The workflow system allows tenants to define custom status workflows for their work orders. Each workflow consists of:

### States
- `id`: Unique identifier for the state
- `label`: Human-readable name
- `is_terminal`: Whether this is a final state

### Transitions
- `from`: Source state ID
- `to`: Destination state ID

## Notes

- All APIs require proper authentication
- Tenant operations are scoped to the authenticated manager
- Slug must be unique across all tenants
- Workflow updates replace the entire workflow configuration
- All timestamps are in ISO 8601 format
- Logo uploads support various formats (base64, file upload, etc.)
