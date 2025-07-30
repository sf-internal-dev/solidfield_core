from django.db import models
from .abstractions import TenantOwnedModel, SoftDeletableModel, BaseModel
from django.utils import timezone

class PermissionLevel(models.TextChoices):
    L1 = "L1", "Field Level"
    L2 = "L2", "Local Control"
    L3 = "L3", "Operational Management"

class TechniciansAggroupment(TenantOwnedModel, BaseModel):
    tag = models.CharField(max_length=1)

    def __str__(self):
        return f"Aggroupment {self.tag}"

class Technician(TenantOwnedModel, SoftDeletableModel):
    username = models.CharField(max_length=12)
    social_name = models.CharField(max_length=150)
    technician_permission = models.CharField(
        max_length=3,
        choices=PermissionLevel.choices
    )
    aggroupment = models.ForeignKey(
        TechniciansAggroupment, 
        on_delete=models.CASCADE, 
        related_name="aggroupment_technician",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.social_name} ({self.username})"


class PermissionFlag(BaseModel):
    level = models.CharField(max_length=2, 
            choices=PermissionLevel.choices)
    action = models.CharField(max_length=100) 
    allowed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("level", "action")

    def __str__(self):
        return f"{self.level} | {self.action} → {'✔' if self.allowed else '✖'}"


class TemporaryDelegation(TenantOwnedModel, BaseModel):
    from_user = models.ForeignKey(
        Technician, 
        on_delete=models.CASCADE, 
        related_name='delegations_given')
    to_user = models.ForeignKey(Technician,
        on_delete=models.CASCADE,
        related_name='delegations_received')
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    def is_active(self):
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.valid_from.date()} up to {self.valid_until.date()})"

class DelegatedAction(BaseModel):
    delegation = models.ForeignKey(
        TemporaryDelegation, 
        on_delete=models.CASCADE, 
        related_name="actions"
        )
    action = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.delegation} → {self.action}"