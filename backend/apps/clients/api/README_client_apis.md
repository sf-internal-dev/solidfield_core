# 📋 **Client APIs Documentation**

## 🎯 **Overview**

This document describes the Client APIs for managing client information, including registration, updates, deletion, and search functionality.

## 🔗 **Base URL**
```
/api/clients/
```

---

## 📝 **API Endpoints**

### **1. ✅ Register Client**
**POST** `/register_client_api/`

Creates a new client or updates an existing one.

#### **Request Body**
```json
{
    "person_type": "individual|company",
    "name": "Client Name",
    "document_id": "12345678901",
    "contact_name": "Contact Person",
    "phone": "+1234567890",
    "email": "client@example.com",
    "country": "US"
}
```

#### **Response**
```json
{
    "success": "Client registered",
    "client_id": "123",
    "messages": []
}
```

---

### **2. ✅ Update Client**
**PUT** `/update_client_api/<int:client_id>/`

Updates an existing client's information.

#### **Request Body**
```json
{
    "person_type": "individual|company",
    "name": "Updated Client Name",
    "document_id": "98765432109",
    "contact_name": "Updated Contact",
    "phone": "+1987654321",
    "email": "updated@example.com",
    "country": "US",
    "is_active": true
}
```

#### **Response**
```json
{
    "success": "Client updated",
    "client_id": "123",
    "messages": []
}
```

---

### **3. ✅ Delete Client**
**DELETE** `/delete_client_api/<int:client_id>/`

Soft deletes a client by setting `is_active` to `false`.

#### **Response**
```json
{
    "success": "Client deleted",
    "client_id": "123",
    "messages": []
}
```

---

### **4. ✅ Search Clients**
**GET** `/search_clients_api/`

Searches for clients with optional filtering and pagination.

#### **Query Parameters**
- `q` (string, optional): Search query for name, email, phone, document, or contact name
- `person_type` (string, optional): Filter by person type (`individual` or `company`)
- `is_active` (boolean, optional): Filter by active status
- `limit` (int, optional): Number of results per page (default: 50)
- `offset` (int, optional): Number of results to skip (default: 0)

#### **Example Request**
```
GET /search_clients_api/?q=john&person_type=individual&is_active=true&limit=20&offset=0
```

#### **Response**
```json
{
    "success": "Clients retrieved",
    "clients": [
        {
            "id": 1,
            "person_type": "individual",
            "name": "John Doe",
            "document_id": "12345678901",
            "contact_name": "John Doe",
            "phone": "+1234567890",
            "email": "john@example.com",
            "country": "US",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ],
    "count": 1,
    "limit": 20,
    "offset": 0,
    "query": "john",
    "messages": []
}
```

---

### **5. ✅ Register Client Address**
**POST** `/register_client_adress_api/`

Registers a new address for a client.

#### **Request Body**
```json
{
    "client": 123,
    "label": "Home",
    "number": "123",
    "complement": "Apt 4B",
    "neighborhood": "Downtown",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "gps_latitude": 40.7128,
    "gps_longitude": -74.0060
}
```

#### **Response**
```json
{
    "success": "Client adress registered",
    "client_adress_id": "456",
    "messages": []
}
```

---

## 🔐 **Permissions Required**

### **Client Management**
- `add_or_update_client`: Required for creating and updating clients
- `delete_client`: Required for deleting clients
- `view_clients`: Required for searching and viewing clients
- `add_client_address`: Required for adding client addresses

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
- `client_not_found`: Client with specified ID not found
- `invalid_person_type`: Invalid person type provided
- `invalid_document_id`: Invalid document ID format
- `invalid_phone_number`: Invalid phone number format
- `invalid_email`: Invalid email format
- `invalid_postal_code`: Invalid postal code format
- `invalid_region_code`: Invalid region/state code
- `invalid_coordinates`: Invalid GPS coordinates

---

## 🔍 **Search Functionality**

The search API supports:
- **Text Search**: Searches across name, email, phone, document_id, and contact_name
- **Filtering**: By person_type and is_active status
- **Pagination**: Using limit and offset parameters
- **Case Insensitive**: All text searches are case-insensitive

---

## 📊 **Data Validation**

### **Client Fields**
- **person_type**: Must be `individual` or `company`
- **name**: Validated for length and character restrictions
- **document_id**: Validated based on country-specific rules
- **phone**: Validated based on country-specific format
- **email**: Standard email format validation
- **contact_name**: Validated for length and character restrictions

### **Address Fields**
- **postal_code**: Validated based on country-specific format
- **state**: Validated based on country-specific region codes
- **coordinates**: Validated for valid latitude/longitude ranges

---

## 🚀 **Usage Examples**

### **Create a New Individual Client**
```bash
curl -X POST /api/clients/register_client_api/ \
  -H "Content-Type: application/json" \
  -d '{
    "person_type": "individual",
    "name": "Jane Smith",
    "document_id": "12345678901",
    "phone": "+1234567890",
    "email": "jane@example.com",
    "country": "US"
  }'
```

### **Search for Active Individual Clients**
```bash
curl -X GET "/api/clients/search_clients_api/?q=smith&person_type=individual&is_active=true"
```

### **Update Client Information**
```bash
curl -X PUT /api/clients/update_client_api/123/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith Updated",
    "phone": "+1987654321"
  }'
```

### **Delete a Client**
```bash
curl -X DELETE /api/clients/delete_client_api/123/
```

---

## 📈 **Performance Notes**

- **Pagination**: Default limit is 50 clients per request
- **Search**: Uses database indexes for efficient text searching
- **Soft Delete**: Clients are soft-deleted (is_active=false) to maintain data integrity
- **Validation**: All validations are performed server-side for security

---

## 🔄 **Integration Notes**

- All APIs require proper authentication and authorization
- Responses include correlation IDs for tracking and debugging
- Error messages are internationalized and user-friendly
- All timestamps are in ISO 8601 format
