from django.db import models
from .abstractions import BaseModel
from .technician import Technician

class OfflineSyncQueue(BaseModel):
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("conflict", "Conflict"), ("success", "Success")])
    payload = models.JSONField()
    
    def __str__(self):
        return f"{self.technician} | {self.status} | {self.created_at.strftime('%Y-%m-%d %H:%M')}"
