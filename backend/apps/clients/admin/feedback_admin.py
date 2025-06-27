from django.contrib import admin
from backend.apps.clients.models.feedback import ClientFeedback, FeedbackLink

class FeedbackLinkInLine(admin.TabularInline):
    model = FeedbackLink
    extra = 0

class ClientFeedbackInLine(admin.ModelAdmin):
    model = ClientFeedback
    extra = 0

