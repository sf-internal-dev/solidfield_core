from django.db import models
from backend.apps.core.models.abstractions import BaseModel

class WorkOrderPhoto(BaseModel):
    work_order = models.ForeignKey("orders.WorkOrder", on_delete=models.CASCADE, related_name="photos")
    uploaded_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    photo_taken_at = models.DateTimeField()
    # Uploaded image
    image = models.ImageField(upload_to="service_photos/")

    # Context/type of photo
    PHOTO_TYPE_CHOICES = [
        ("before", "Before Execution"),
        ("after", "After Execution"),
        ("issue", "Issue/Failure Identified"),
        ("proof", "Proof of Service"),
        ("custom", "Custom"),
    ]
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPE_CHOICES)

    # Optional description
    description = models.TextField(blank=True)

    # Metadata
    gps_latitude = models.FloatField(null=True, blank=True)
    gps_longitude = models.FloatField(null=True, blank=True)
    device_info = models.CharField(max_length=100, blank=True)

    add_watermark = models.BooleanField(default=True)
    watermark_has_company_logo = models.BooleanField(default=False)
    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.work_order.identifier} - {self.photo_type} by {self.uploaded_by}"
