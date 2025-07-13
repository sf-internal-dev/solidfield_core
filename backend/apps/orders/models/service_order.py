from django.db import models
from backend.apps.core.models.abstractions import TenantOwnedModel, BaseModel
from django.core.exceptions import ValidationError
from django.utils import timezone

class ServiceOrder(TenantOwnedModel):
    identifier = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT, related_name="created_orders")
    assigned_to = models.ForeignKey("core.Technician", on_delete=models.PROTECT, related_name="assigned_orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50)
    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.SET_NULL)
    client_name = models.CharField(max_length=200, blank=True)  # Nome livre preenchido na hora
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=30, blank=True)

    # Auto-tracking for audit (optional)
    status_history = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Service Order #{self.identifier} - {self.status.replace('_', ' ').title()}"

class ServiceOrderDownloadLink(models.Model):
    service_order = models.ForeignKey("ServiceOrder", on_delete=models.CASCADE)
    key = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey("core.Technician", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    purpose = models.CharField(max_length=100, blank=True)  # ex: "cliente-avaliacao", "recibo"

    def __str__(self):
        short_key = self.key[:8] + "..." if self.key else "no-key"
        return f"PDF Link [{short_key}] - Order #{self.service_order.identifier} - Purpose: {self.purpose or 'unspecified'}"