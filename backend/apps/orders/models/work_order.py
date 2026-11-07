from django.db import models
from backend.apps.core.models.abstractions import TenantOwnedModel, BaseModel
from django.core.exceptions import ValidationError
from django.utils import timezone

class WorkOrder(TenantOwnedModel):
    identifier = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT, related_name="created_orders")
    assigned_to = models.ForeignKey("core.Technician", on_delete=models.PROTECT, related_name="assigned_orders", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Work order details
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='pending')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    # new fields patch
    first_access = models.BooleanField(default=False)
    work_start = models.DateTimeField(blank=True,null=True)
    work_end = models.DateTimeField(blank=True,null=True)
    has_remaining_work = models.BooleanField(default=False)
    #-=-=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    status = models.CharField(max_length=50)
    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.SET_NULL)
    client_name = models.CharField(max_length=200, blank=True)  # Free-form name filled in at the time
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=30, blank=True)

    # Auto-tracking for audit
    status_history = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Work Order #{self.identifier} - {self.status.replace('_', ' ').title()}"


class WorkOrderStatusHistory(models.Model):
    work_order = models.ForeignKey("WorkOrder", on_delete=models.CASCADE, related_name="workorderstatushistory_set")
    status = models.CharField(max_length=50)
    changed_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Work Order Status History"
        verbose_name_plural = "Work Order Status Histories"

    def __str__(self):
        return f"Status: {self.status} - Order #{self.work_order.identifier} - {self.created_at}"


class WorkOrderDownloadLink(models.Model):
    work_order = models.ForeignKey("WorkOrder", on_delete=models.CASCADE)
    key = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey("core.Technician", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    purpose = models.CharField(max_length=100, null=True, blank=True) 

    def __str__(self):
        short_key = self.key[:8] + "..." if self.key else "no-key"
        return f"PDF Link [{short_key}] - Order #{self.work_order.identifier} - Purpose: {self.purpose or 'unspecified'}"