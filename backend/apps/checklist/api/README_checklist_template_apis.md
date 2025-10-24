# 📋 **Checklist Template APIs Documentation**

## 🎯 **Overview**

This document describes the Checklist Template APIs for managing checklist templates, including creation, delegation, versioning, and order management.

## 🔗 **Base URL**
```
/api/checklist-templates/
```

---

## 📝 **API Endpoints**

### **1. ✅ Create Checklist Template**
**POST** `/create_checklist_template_api/`

Creates a new checklist template.

#### **Request Body**
```json
{
    "name": "Maintenance Checklist",
    "service_type": "maintenance",
    "is_global": true,
    "version": 1
}
```

#### **Response**
```json
{
    "success": "Checklist Template registered",
    "checklist_template_id": "123",
    "messages": []
}
```

---

### **2. ✅ Create Checklist Item Template**
**POST** `/create_checklist_item_template_api/`

Adds a new item to a checklist template.

#### **Request Body**
```json
{
    "template": 123,
    "order": 1,
    "question": "Is the equipment functioning properly?",
    "answer_type": "boolean",
    "is_required": true,
    "choice_options": ""
}
```

#### **Response**
```json
{
    "success": "Checklist Item Template registered",
    "checklist_item_template_id": "456",
    "messages": []
}
```

---

### **3. ✅ Get Next Order for Template**
**GET** `/get_next_order_for_template_api/<int:template_id>/`

Retrieves the next available order number for a template.

#### **Response**
```json
{
    "success": "Next order retrieved",
    "template_id": 123,
    "next_order": 3,
    "messages": []
}
```

---

### **4. ✅ Delegate Template to Aggroupment**
**POST** `/delegate_checklist_template_to_aggroupment_api/<int:template_id>/`

Delegates a checklist template to a technician aggroupment.

#### **Request Body**
```json
{
    "aggroupment_id": 789
}
```

#### **Response**
```json
{
    "success": "Template delegated to aggroupment",
    "template_id": "123",
    "aggroupment_id": "789",
    "is_global": false,
    "messages": []
}
```

---

### **5. ✅ Remove Aggroupment from Template**
**DELETE** `/remove_aggroupment_from_template_api/<int:template_id>/<int:aggroupment_id>/`

Removes a technician aggroupment from a checklist template.

#### **Response**
```json
{
    "success": "Aggroupment removed from template",
    "template_id": "123",
    "aggroupment_id": "789",
    "messages": []
}
```

---

### **6. ✅ Update Template Version**
**POST** `/update_checklist_template_version_api/<int:template_id>/`

Creates a new version of a checklist template with optional modifications.

#### **Request Body**
```json
{
    "orders_to_remove": [1, 3],
    "items_to_add": [
        {
            "question": "New question?",
            "answer_type": "text",
            "is_required": true,
            "choice_options": "",
            "order": 2
        }
    ],
    "copy_aggroupments": true,
    "deactivate_previous": true
}
```

#### **Response**
```json
{
    "success": "Template version updated",
    "original_template_id": "123",
    "new_template_id": "124",
    "new_version": 2,
    "is_global": false,
    "is_active": true,
    "messages": []
}
```

---

## 🔐 **Permissions Required**

### **Template Management**
- `create_checklist_template`: Required for creating templates
- `add_item_to_checklist_template`: Required for adding items
- `delegate_checklist_template_to_aggroupment`: Required for delegation
- `remove_aggroupment_from_template`: Required for removing aggroupments
- `update_checklist_template_version`: Required for versioning

---

## ⚠️ **Error Handling**

All APIs return standardized error responses:

```json
{
    "codes": ["error_code_1", "error_code_2"],
    "correlation_id": "uuid-correlation-id"
}
```

### **Common Error Codes**
- `template_not_found`: Template with specified ID not found
- `aggroupment_not_found`: Aggroupment with specified ID not found
- `would_violate_min_groups`: Cannot remove aggroupment (would leave template with no groups)
- `item_not_found_by_order:{order}`: Item with specified order not found
- `invalid_template_name_length`: Template name length is invalid
- `invalid_template_name_chars`: Template name contains invalid characters
- `invalid_service_type_length`: Service type length is invalid
- `invalid_service_type_chars`: Service type contains invalid characters
- `invalid_is_active_type`: is_active field must be boolean
- `invalid_is_global_type`: is_global field must be boolean
- `invalid_aggroupments_type`: aggroupments field must be a list
- `invalid_aggroupment_id`: Invalid aggroupment ID
- `invalid_version_value`: Invalid version value
- `invalid_order_value`: Invalid order value
- `invalid_question_length`: Question length is invalid
- `invalid_question_chars`: Question contains invalid characters
- `invalid_answer_type`: Answer type is invalid
- `invalid_required_type`: Required field must be boolean
- `empty_choice_options`: Choice options cannot be empty
- `choice_option_too_long`: Choice option is too long
- `invalid_choice_option_chars`: Choice option contains invalid characters

---

## 🔧 **Template Management Features**

### **✅ Template Creation**
- **Basic Information**: Name, service type, version
- **Global vs Local**: Templates can be global or group-specific
- **Version Control**: Automatic versioning system

### **✅ Item Management**
- **Order Management**: Automatic order assignment
- **Question Types**: Support for boolean, text, choice, number
- **Validation**: Comprehensive field validation
- **Required Fields**: Optional and required question support

### **✅ Delegation System**
- **Aggroupment Assignment**: Assign templates to technician groups
- **Global to Local**: Convert global templates to group-specific
- **Multiple Groups**: Support for multiple aggroupment assignments

### **✅ Version Control**
- **Version Creation**: Create new versions of existing templates
- **Item Management**: Add/remove items in new versions
- **Aggroupment Copying**: Copy aggroupments to new versions
- **Previous Deactivation**: Option to deactivate previous versions

---

## 🔍 **Order Management**

### **✅ Automatic Order Assignment**
- **Next Order Function**: Automatically calculates next available order
- **Uniqueness Validation**: Ensures order uniqueness within template
- **Conflict Resolution**: Handles order conflicts gracefully

### **✅ Order Validation**
- **Within Template**: Orders must be unique within each template
- **Sequential Assignment**: Automatic sequential numbering
- **Manual Override**: Support for manual order specification

---

## 📊 **Template Lifecycle**

### **1. Creation**
- Create template with basic information
- Set global/local status
- Assign initial version

### **2. Item Addition**
- Add items with questions and types
- Set order and requirements
- Configure choice options

### **3. Delegation**
- Assign to technician aggroupments
- Convert global to local if needed
- Manage multiple assignments

### **4. Versioning**
- Create new versions for updates
- Modify items (add/remove)
- Copy aggroupments
- Deactivate previous versions

### **5. Maintenance**
- Remove aggroupments
- Update item properties
- Manage template status

---

## 🚀 **Usage Examples**

### **Create a Maintenance Template**
```bash
curl -X POST /api/checklist-templates/create_checklist_template_api/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Equipment Maintenance",
    "service_type": "maintenance",
    "is_global": true
  }'
```

### **Add Items to Template**
```bash
curl -X POST /api/checklist-templates/create_checklist_item_template_api/ \
  -H "Content-Type: application/json" \
  -d '{
    "template": 123,
    "question": "Is equipment clean?",
    "answer_type": "boolean",
    "is_required": true
  }'
```

### **Delegate Template to Group**
```bash
curl -X POST /api/checklist-templates/delegate_checklist_template_to_aggroupment_api/123/ \
  -H "Content-Type: application/json" \
  -d '{
    "aggroupment_id": 456
  }'
```

### **Create New Version**
```bash
curl -X POST /api/checklist-templates/update_checklist_template_version_api/123/ \
  -H "Content-Type: application/json" \
  -d '{
    "orders_to_remove": [1],
    "items_to_add": [
      {
        "question": "Updated question?",
        "answer_type": "text",
        "is_required": true,
        "order": 2
      }
    ],
    "copy_aggroupments": true,
    "deactivate_previous": true
  }'
```

---

## 🔄 **Integration Notes**

- All APIs require proper authentication and authorization
- Responses include correlation IDs for tracking and debugging
- Error messages are internationalized and user-friendly
- All timestamps are in ISO 8601 format
- Template operations are atomic and transactional

---

## 📋 **Data Models**

### **ChecklistTemplate**
- `id`: Unique identifier
- `name`: Template name
- `service_type`: Type of service
- `version`: Version number
- `is_global`: Global or local template
- `is_active`: Active status
- `created_by`: Creator technician
- `tenant`: Associated tenant

### **ChecklistItemTemplate**
- `id`: Unique identifier
- `template`: Associated template
- `order`: Item order within template
- `question`: Question text
- `answer_type`: Type of answer (boolean, text, choice, number)
- `required`: Whether item is required
- `choice_options`: Options for choice type

### **TechniciansAggroupment**
- `id`: Unique identifier
- `name`: Group name
- `tenant`: Associated tenant
