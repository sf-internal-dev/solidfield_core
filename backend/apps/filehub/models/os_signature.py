from django.db import models
from backend.apps.core.models.abstractions import BaseModel

class ServiceOrderSignature(BaseModel):
    service_order = models.ForeignKey("orders.ServiceOrder", on_delete=models.CASCADE, related_name="signature")
    ordered_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT)
    signed_at = models.DateTimeField(auto_now_add=True)

    image = models.ImageField(upload_to="signatures/")

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["signed_at"]
