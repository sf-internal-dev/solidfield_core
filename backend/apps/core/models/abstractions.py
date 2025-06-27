from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class TenantOwnedModel(BaseModel):
    tenant = models.ForeignKey("core.CompanyTenant", on_delete=models.PROTECT)
    class Meta:
        abstract = True


class SoftDeletableModel(models.Model):
    is_active = models.BooleanField(default=True)
    class Meta:
        abstract = True 