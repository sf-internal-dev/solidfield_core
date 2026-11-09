from django.db import models
from .abstractions import BaseModel
from .technician import Technician


class OfflineSyncQueue(BaseModel):
    """Queue of mutations made offline; the client applies `process` when there is a network."""

    technician = models.ForeignKey(
        Technician,
        on_delete=models.CASCADE,
        related_name="offline_sync_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("conflict", "Conflict"),
            ("success", "Success"),
        ],
    )
    payload = models.JSONField()
    client_mutation_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Idempotency: the same value + the same technician does not duplicate success (e.g. app UUID).",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["technician", "client_mutation_id"],
                condition=models.Q(client_mutation_id__isnull=False)
                & ~models.Q(client_mutation_id=""),
                name="core_offlinesyncqueue_technician_clientmutation_uidx",
            ),
        ]

    def __str__(self):
        return f"{self.technician} | {self.status} | {self.created_at.strftime('%Y-%m-%d %H:%M')}"
