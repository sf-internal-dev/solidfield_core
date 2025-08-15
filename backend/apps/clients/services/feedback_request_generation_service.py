from backend.apps.clients.utils.feedback.feedback_request_generation_util import generate_feedback_request_key, feedback_request_link
from backend.apps.clients.utils.feedback.feedback_validation_util import (
    stars_given, reached_comment_max_characters, feedback_preview, 
)
from backend.apps.clients.models.feedback import FeedbackLink, ClientFeedback
from backend.apps.clients.models.client import Client
from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.core.services.audition_log_service import log_service_order_feedback_received
from typing import Tuple, Optional, List
from django.db import IntegrityError

# -> Generates and assigns a unique feedback request key to a given FeedbackLink
# Tries to save the key and returns an error if a conflict occurs in the database
# Returns the updated FeedbackLink instance or None with an error list if failed
def add_key_for_feedback_request(feedback_link: FeedbackLink) -> Tuple[Optional[FeedbackLink], List[str]]:
    errors = []
    try:
        key = generate_feedback_request_key()
        feedback_link.key = key
        feedback_link.save()
        return feedback_link, errors
    except IntegrityError:
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
def create_client_feedback(service_order: ServiceOrder, client: Client, client_name: str,
    client_email: str, stars: int, comment: str, strengths)-> Tuple[Optional[ClientFeedback], List[str]]:
    
    errors = []

    client_stars, feedback_label = stars_given(stars)
    if client_stars is None:
        errors.append("invalid_stars_value")
        return None, errors
    
    if reached_comment_max_characters(comment):
        errors.append("comment_too_long")
        return None, errors
    
    log_service_order_feedback_received(service_order, feedback_label)

    if not reached_comment_max_characters(comment):
        if client:
            client_feedback = ClientFeedback.objects.create(
                service_order=service_order,
                client=client,
                client_name=client.client_name,
                client_email=client.client_email,
                stars = client_stars,
                strengths = strengths if strengths else None,
            )
        client_feedback = ClientFeedback.objects.create(
                service_order=service_order,
                client_name=client_name,
                client_email=client_email,
                stars = client_stars,
                strengths = strengths if strengths else None,
            )
    return client_feedback
