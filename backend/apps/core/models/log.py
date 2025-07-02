
from django.db import models
from .abstractions import BaseModel, TenantOwnedModel
from .technician import Technician
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# auditlog terá um util nesse reference id que reconhecerá o modelo relacionado ao action
# o action por sua vez um esquema (provavelmente como workflow json) pra relacionar cada action com algum modelo
# reconhecendo por exemplo action: status_transition model: service order, então eu vou relacionar o reference id com o model 
# pra acesso
class AuditLog(TenantOwnedModel):
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=150)  # Ex: "status_update", "photo_upload"
    # Esse reference_id pode ser pra varias coisas, como a ServiceOrder quando mudar um status e também 
    # TemporaryDelegation quando for feita um delegação de permissão
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    reference = GenericForeignKey("content_type", "object_id")
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at.date()} | {self.technician} → {self.action} (ref: {self.reference_id})"
