from django.db import models
from .abstractions import TenantOwnedModel

class CompanyTenant(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True) 
    tenant_code = models.CharField(max_length=10,unique=True,db_index=True,editable=False)
    is_active = models.BooleanField(default=True)
    
    primary_contact_name = models.CharField(max_length=100, blank=True)
    primary_contact_email = models.EmailField(blank=True)
    primary_contact_phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    billing_account_id = models.CharField(max_length=100, blank=True, null=True) 

    owner = models.OneToOneField(
        "core.AccountHolderUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_tenant"
    )

    country = models.CharField(max_lenght=3,default="USA")
    locale = models.CharField(max_length=10, default="en-US")
    timezone = models.CharField(max_length=50, default="America/Los_Angeles")

    logo = models.ImageField(upload_to="tenant_logos/", null=True, blank=True)
    color_primary = models.CharField(max_length=7, default="#000000") 

    class Meta:
        verbose_name = "Company / Tenant"
        verbose_name_plural = "Companies / Tenants"

    def __str__(self):
        return f"{self.name} ({self.tenant_code})"

class TenantStatusWorkflow(TenantOwnedModel):
    tenant = models.OneToOneField(
        "core.CompanyTenant",
        on_delete=models.CASCADE,
        related_name="status_workflow" 
    )
    workflow_json = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant.name} Workflow - Updated at {self.updated_at.date()}"

