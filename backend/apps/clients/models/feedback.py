from django.db import models
from backend.apps.core.models.abstractions import BaseModel

class ClientFeedback(BaseModel):
    service_order = models.OneToOneField("orders.ServiceOrder", on_delete=models.CASCADE)

    client = models.ForeignKey("Client", null=True, blank=True, on_delete=models.SET_NULL)

    client_name = models.CharField(max_length=200, blank=True)
    client_email = models.EmailField(blank=True)

    stars = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

import secrets

class FeedbackLink(BaseModel):
    service_order = models.OneToOneField("orders.ServiceOrder", on_delete=models.CASCADE)
    key = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    # def save(self, *args, **kwargs):
    #     if not self.key:
    #         self.key = secrets.token_urlsafe(12)[:20]
    #     super().save(*args, **kwargs)
