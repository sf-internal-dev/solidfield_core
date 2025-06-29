
from django.db import models
from .abstractions import BaseModel, TenantOwnedModel
from .technician import Technician

class AuditLog(TenantOwnedModel):
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=150)  # Ex: "status_update", "photo_upload"
    reference_id = models.CharField(max_length=100)  # Pode ser ID da OS, checklist, etc
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at.date()} | {self.technician} → {self.action} (ref: {self.reference_id})"
