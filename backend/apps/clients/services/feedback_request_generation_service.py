from backend.apps.clients.utils.feedback.feedback_request_generation_util import generate_feedback_request_key, feedback_request_link
from backend.apps.clients.utils.feedback.feedback_validation_util import (
    stars_given, reached_comment_max_characters, feedback_preview, is_positive_feedback,
    extract_keywords_en, get_generic_keywords,
)
from backend.apps.clients.models.feedback import FeedbackLink, ClientFeedback
from backend.apps.clients.models.client import Client
from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.core.services.audition_log_service import log_service_order_feedback_received

def add_key_for_feedback_request(feedback_link: FeedbackLink):
    key = generate_feedback_request_key()
    feedback_link.key = key
    feedback_link.save()
    return feedback_link

def return_feedback_preview(feedback: ClientFeedback):
    return feedback_preview(feedback)

def create_client_feedback(service_order: ServiceOrder, client: Client, client_name: str,
                        client_email: str, stars: int, comment: str, strengths):
    client_stars, feedback_label = stars_given(stars)
    is_positive = is_positive_feedback(client_stars)
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

"""
class ClientFeedback(BaseModel):
    service_order = models.OneToOneField("orders.ServiceOrder", on_delete=models.CASCADE)

    client = models.ForeignKey("Client", null=True, blank=True, on_delete=models.SET_NULL)

    client_name = models.CharField(max_length=200, blank=True)
    client_email = models.EmailField(blank=True)

    stars = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
"""