
from django.db import models
from .abstractions import BaseModel, TenantOwnedModel
from .technician import Technician
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# auditlog will have a util on this reference id that recognizes the model related to the action
# the action will in turn have a schema (probably like workflow json) to relate each action to some model
# recognizing for example action: status_transition model: service order, then I will relate the reference id to the model
# for access
class AuditLog(TenantOwnedModel):
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=150)  # Ex: "status_update", "photo_upload"
    # This reference_id can be for several things, such as the ServiceOrder when a status changes and also
    # TemporaryDelegation when a permission delegation is made
    content_type = models.ForeignKey(ContentType,null=True,blank=True, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    reference = GenericForeignKey("content_type", "object_id")
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at.date()} | {self.technician} → {self.action} (ref: {self.reference_id})"

