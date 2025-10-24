from backend.apps.clients.utils.feedback.feedback_request_generation_util import generate_feedback_request_key, feedback_request_link
from backend.apps.clients.utils.feedback.feedback_validation_util import (
    stars_given, reached_comment_max_characters, feedback_preview, 
)
from backend.apps.clients.models.feedback import FeedbackLink, ClientFeedback
from backend.apps.clients.models.client import Client
from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.core.models.technician import Technician
from backend.apps.orders.models.work_order import WorkOrder

from backend.apps.core.services.audition_log_service import log_work_order_feedback_received
from typing import Tuple, Optional, List, Dict, Any
from django.db import IntegrityError
from django.db.models import Q, Avg, Count, Case, When, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
from backend.apps.core.services.technician_permission_service import has_permission

def create_feedback_link(
    technician_operating: Technician, 
    work_order: WorkOrder,
) -> Tuple[Optional[FeedbackLink], List[str]]:
    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "generate_feedback_link")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

    for _ in range(5):  # up to 5 tries
        try:
            key = generate_feedback_request_key()
            feedback_link = FeedbackLink.objects.create(
                work_order=work_order,
                key=key
            )
            return feedback_link, errors
        except IntegrityError:
            continue

    errors.append("key_generation_failed")
    return None, errors


# -> Builds and returns a preview structure for a given ClientFeedback
# Uses the feedback_preview utility to assemble the preview
# Does not perform validation or error handling
def return_feedback_preview(feedback: ClientFeedback):
    return feedback_preview(feedback)

# -> Creates a ClientFeedback entry for a given ServiceOrder and client information
# Validates star rating and comment length before saving
# Logs the feedback reception in the service order history
# Returns the created ClientFeedback or None with an error list if validation or save fails
def create_client_feedback(technician_operating: Technician, work_order: WorkOrder, client: Client, client_name: str,
    client_email: str, stars: int, comment: str, strengths)-> Tuple[Optional[ClientFeedback], List[str]]:
    
    errors = []

    ok, perm_errors = has_permission(technician_operating, "create_client_feedback")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

    client_stars, feedback_label = stars_given(stars)
    if client_stars is None:
        errors.append("invalid_stars_value")
        return None, errors
    
    if reached_comment_max_characters(comment):
        errors.append("comment_too_long")
        return None, errors
    
    log_work_order_feedback_received(tenant=technician_operating.tenant, work_order=work_order, feedback_label=feedback_label)

    if not reached_comment_max_characters(comment):
        if client:
            client_feedback = ClientFeedback.objects.create(
                work_order=work_order,
                client=client,
                client_name=client.name,
                client_email=client.email,
                stars = client_stars,
                strengths = strengths if strengths else None,
            )
        client_feedback = ClientFeedback.objects.create(
                work_order=work_order,
                client_name=client_name,
                client_email=client_email,
                stars = client_stars,
                strengths = strengths if strengths else None,
            )
    return client_feedback

# -> Lists feedback entries with optional filtering and pagination
# Supports filtering by work order, client, date range, and star rating
# Returns a list of feedback entries with basic information
def list_feedback(technician_operating: Technician, work_order_id: Optional[int] = None,
                 client_id: Optional[int] = None, min_stars: Optional[int] = None,
                 max_stars: Optional[int] = None, date_from: Optional[datetime] = None,
                 date_to: Optional[datetime] = None, limit: int = 50, offset: int = 0) -> Tuple[List[ClientFeedback], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_feedback")
    if not ok:
        return [], perm_errors
    
    # Build query
    queryset = ClientFeedback.objects.filter(work_order__tenant=technician_operating.tenant)
    
    # Apply filters
    if work_order_id:
        queryset = queryset.filter(work_order_id=work_order_id)
    
    if client_id:
        queryset = queryset.filter(client_id=client_id)
    
    if min_stars is not None:
        queryset = queryset.filter(stars__gte=min_stars)
    
    if max_stars is not None:
        queryset = queryset.filter(stars__lte=max_stars)
    
    if date_from:
        queryset = queryset.filter(submitted_at__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(submitted_at__lte=date_to)
    
    # Apply pagination and ordering
    feedback_list = list(queryset.order_by('-submitted_at')[offset:offset + limit])
    
    return feedback_list, errors

# -> Generates comprehensive analytics for feedback data
# Calculates average ratings, distribution, trends, and other metrics
# Returns detailed analytics data for reporting and insights
def get_feedback_analytics(technician_operating: Technician, work_order_id: Optional[int] = None,
                          client_id: Optional[int] = None, date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None) -> Tuple[Dict[str, Any], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_feedback_analytics")
    if not ok:
        return {}, perm_errors
    
    # Build base query
    queryset = ClientFeedback.objects.filter(work_order__tenant=technician_operating.tenant)
    
    # Apply filters
    if work_order_id:
        queryset = queryset.filter(work_order_id=work_order_id)
    
    if client_id:
        queryset = queryset.filter(client_id=client_id)
    
    if date_from:
        queryset = queryset.filter(submitted_at__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(submitted_at__lte=date_to)
    
    # Calculate basic metrics
    total_feedback = queryset.count()
    
    if total_feedback == 0:
        return {
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {},
            "recent_trends": {},
            "top_work_orders": [],
            "feedback_with_comments": 0,
            "feedback_with_strengths": 0
        }, errors
    
    # Average rating
    average_rating = queryset.aggregate(avg_rating=Avg('stars'))['avg_rating'] or 0
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        count = queryset.filter(stars=i).count()
        rating_distribution[f"{i}_star"] = count
    
    # Recent trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_feedback = queryset.filter(submitted_at__gte=thirty_days_ago)
    
    # Group by day for trend analysis
    trends = {}
    for i in range(30):
        date = timezone.now() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_feedback = recent_feedback.filter(submitted_at__gte=day_start, submitted_at__lt=day_end)
        day_avg = day_feedback.aggregate(avg_rating=Avg('stars'))['avg_rating'] or 0
        
        trends[day_start.strftime('%Y-%m-%d')] = {
            "count": day_feedback.count(),
            "average_rating": round(day_avg, 2)
        }
    
    # Top work orders by feedback count
    top_work_orders = queryset.values('work_order__identifier', 'work_order__title').annotate(
        feedback_count=Count('id'),
        avg_rating=Avg('stars')
    ).order_by('-feedback_count')[:10]
    
    # Feedback with comments and strengths
    feedback_with_comments = queryset.exclude(comment='').count()
    feedback_with_strengths = queryset.exclude(strengths='').count()
    
    # Monthly breakdown
    monthly_data = {}
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        month_feedback = queryset.filter(submitted_at__gte=month_start, submitted_at__lt=month_end)
        month_avg = month_feedback.aggregate(avg_rating=Avg('stars'))['avg_rating'] or 0
        
        monthly_data[month_start.strftime('%Y-%m')] = {
            "count": month_feedback.count(),
            "average_rating": round(month_avg, 2)
        }
    
    analytics = {
        "total_feedback": total_feedback,
        "average_rating": round(average_rating, 2),
        "rating_distribution": rating_distribution,
        "recent_trends": trends,
        "monthly_breakdown": monthly_data,
        "top_work_orders": list(top_work_orders),
        "feedback_with_comments": feedback_with_comments,
        "feedback_with_strengths": feedback_with_strengths,
        "comment_percentage": round((feedback_with_comments / total_feedback) * 100, 2) if total_feedback > 0 else 0,
        "strengths_percentage": round((feedback_with_strengths / total_feedback) * 100, 2) if total_feedback > 0 else 0
    }
    
    return analytics, errors
