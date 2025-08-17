from django.db import models
from backend.apps.core.models.abstractions import BaseModel

class WorkOrderSignature(BaseModel):
    work_order = models.ForeignKey("orders.WorkOrder", on_delete=models.CASCADE, related_name="signature")
    ordered_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT)
    signed_by = models.CharField(max_length=40)

    signed_at = models.DateTimeField(auto_now_add=True)

    image = models.ImageField(upload_to="signatures/")

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["signed_at"]

    def __str__(self):
        return f"{self.work_order.identifier} - signed by {self.signed_by} - ordered by {self.ordered_by}"
