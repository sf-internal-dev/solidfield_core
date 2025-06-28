import nested_admin
from django.contrib import admin
from backend.apps.clients.models.feedback import ClientFeedback, FeedbackLink

class FeedbackLinkInLine(nested_admin.NestedStackedInline):
    model = FeedbackLink
    extra = 0

class ClientFeedbackInLine(nested_admin.NestedStackedInline):
    inliines = [FeedbackLinkInLine]
    model = ClientFeedback
    extra = 0

