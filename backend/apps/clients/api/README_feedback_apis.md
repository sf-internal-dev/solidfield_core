# 📊 **Feedback APIs Documentation**

## 🎯 **Overview**

This document describes the Feedback APIs for managing client feedback, including listing feedback entries and generating comprehensive analytics.

## 🔗 **Base URL**
```
/api/feedback/
```

---

## 📝 **API Endpoints**

### **1. ✅ List Feedback**
**GET** `/list_feedback_api/`

Retrieves a list of feedback entries with optional filtering and pagination.

#### **Query Parameters**
- `work_order_id` (int, optional): Filter by work order ID
- `client_id` (int, optional): Filter by client ID
- `min_stars` (int, optional): Minimum star rating (1-5)
- `max_stars` (int, optional): Maximum star rating (1-5)
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)
- `limit` (int, optional): Number of results per page (default: 50)
- `offset` (int, optional): Number of results to skip (default: 0)

#### **Example Request**
```
GET /list_feedback_api/?work_order_id=123&min_stars=4&date_from=2024-01-01T00:00:00Z&limit=20&offset=0
```

#### **Response**
```json
{
    "success": "Feedback retrieved",
    "feedback": [
        {
            "id": 1,
            "client_name": "John Doe",
            "client_email": "john@example.com",
            "stars": 5,
            "comment": "Excellent service!",
            "strengths": "Professional and timely",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "count": 1,
    "limit": 20,
    "offset": 0,
    "messages": []
}
```

---

### **2. ✅ Get Feedback Analytics**
**GET** `/get_feedback_analytics_api/`

Generates comprehensive analytics and insights from feedback data.

#### **Query Parameters**
- `work_order_id` (int, optional): Filter by work order ID
- `client_id` (int, optional): Filter by client ID
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

#### **Example Request**
```
GET /get_feedback_analytics_api/?date_from=2024-01-01T00:00:00Z&date_to=2024-12-31T23:59:59Z
```

#### **Response**
```json
{
    "success": "Feedback analytics retrieved",
    "analytics": {
        "total_feedback": 150,
        "average_rating": 4.2,
        "rating_distribution": {
            "1_star": 5,
            "2_star": 8,
            "3_star": 15,
            "4_star": 45,
            "5_star": 77
        },
        "recent_trends": {
            "2024-01-15": {
                "count": 3,
                "average_rating": 4.5
            },
            "2024-01-14": {
                "count": 2,
                "average_rating": 4.0
            }
        },
        "monthly_breakdown": {
            "2024-01": {
                "count": 25,
                "average_rating": 4.1
            },
            "2023-12": {
                "count": 30,
                "average_rating": 4.3
            }
        },
        "top_work_orders": [
            {
                "work_order__identifier": "WO-001",
                "work_order__title": "Maintenance Service",
                "feedback_count": 15,
                "avg_rating": 4.5
            }
        ],
        "feedback_with_comments": 120,
        "feedback_with_strengths": 95,
        "comment_percentage": 80.0,
        "strengths_percentage": 63.33
    },
    "messages": []
}
```

---

### **3. ✅ Create Feedback Link**
**POST** `/create_feedback_link_api/`

Creates a feedback link for a work order.

#### **Request Body**
```json
{
    "work_order": 123
}
```

#### **Response**
```json
{
    "success": "Feedback Link registered",
    "feedback_link_id": "456",
    "messages": []
}
```

---

### **4. ✅ Create Client Feedback**
**POST** `/create_client_feedback_api/`

Creates a new client feedback entry.

#### **Request Body**
```json
{
    "work_order": 123,
    "client": 789,
    "client_name": "John Doe",
    "client_email": "john@example.com",
    "stars": 5,
    "comment": "Excellent service!",
    "strenghts": "Professional and timely"
}
```

#### **Response**
```json
{
    "success": "Client Feedback registered",
    "client_feedback_id": "101",
    "messages": []
}
```

---

## 🔐 **Permissions Required**

### **Feedback Management**
- `generate_feedback_link`: Required for creating feedback links
- `create_client_feedback`: Required for creating feedback entries
- `view_feedback`: Required for listing feedback
- `view_feedback_analytics`: Required for viewing analytics

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
- `key_generation_failed`: Failed to generate unique feedback key
- `invalid_stars_value`: Invalid star rating value
- `comment_too_long`: Comment exceeds maximum length
- `service_order_required`: Service order is required
- `client_name_too_long`: Client name is too long
- `client_email_invalid`: Invalid client email format
- `stars_required`: Star rating is required
- `stars_out_of_range`: Star rating is out of range (1-5)
- `stars_not_integer`: Star rating must be an integer
- `comment_not_string`: Comment must be a string
- `strengths_not_string`: Strengths field must be a string

---

## 📊 **Analytics Features**

### **Basic Metrics**
- **Total Feedback Count**: Total number of feedback entries
- **Average Rating**: Overall average star rating
- **Rating Distribution**: Breakdown by star rating (1-5 stars)

### **Trend Analysis**
- **Recent Trends**: Daily feedback trends for the last 30 days
- **Monthly Breakdown**: Monthly feedback statistics for the last 12 months
- **Date Range Filtering**: Custom date range analysis

### **Performance Insights**
- **Top Work Orders**: Work orders with most feedback
- **Comment Analysis**: Percentage of feedback with comments
- **Strengths Analysis**: Percentage of feedback with strengths

### **Advanced Filtering**
- **Work Order Filtering**: Analytics for specific work orders
- **Client Filtering**: Analytics for specific clients
- **Date Range Filtering**: Custom time period analysis

---

## 🔍 **Search and Filtering**

### **List Feedback Features**
- **Work Order Filtering**: Filter by specific work order
- **Client Filtering**: Filter by specific client
- **Rating Range**: Filter by minimum/maximum star rating
- **Date Range**: Filter by submission date range
- **Pagination**: Efficient pagination with limit/offset

### **Analytics Filtering**
- **Work Order Analytics**: Focus on specific work order performance
- **Client Analytics**: Analyze feedback patterns for specific clients
- **Time-based Analysis**: Custom date range for trend analysis

---

## 📈 **Performance Notes**

- **Pagination**: Default limit is 50 feedback entries per request
- **Analytics**: Optimized queries with database aggregations
- **Caching**: Consider implementing caching for frequently accessed analytics
- **Date Parsing**: Supports ISO 8601 date format with timezone handling

---

## 🚀 **Usage Examples**

### **Get Recent High-Rating Feedback**
```bash
curl -X GET "/api/feedback/list_feedback_api/?min_stars=4&date_from=2024-01-01T00:00:00Z&limit=10"
```

### **Get Monthly Analytics**
```bash
curl -X GET "/api/feedback/get_feedback_analytics_api/?date_from=2024-01-01T00:00:00Z&date_to=2024-01-31T23:59:59Z"
```

### **Get Work Order Specific Feedback**
```bash
curl -X GET "/api/feedback/list_feedback_api/?work_order_id=123"
```

### **Get Client Analytics**
```bash
curl -X GET "/api/feedback/get_feedback_analytics_api/?client_id=456"
```

---

## 🔄 **Integration Notes**

- All APIs require proper authentication and authorization
- Responses include correlation IDs for tracking and debugging
- Error messages are internationalized and user-friendly
- All timestamps are in ISO 8601 format
- Analytics data is calculated in real-time for accuracy

---

## 📋 **Data Models**

### **ClientFeedback**
- `id`: Unique identifier
- `work_order`: Associated work order
- `client`: Associated client (optional)
- `client_name`: Client name
- `client_email`: Client email
- `stars`: Star rating (1-5)
- `comment`: Feedback comment
- `strengths`: Client strengths
- `submitted_at`: Submission timestamp

### **FeedbackLink**
- `id`: Unique identifier
- `work_order`: Associated work order
- `key`: Unique link key
- `created_at`: Creation timestamp
- `used`: Usage status
