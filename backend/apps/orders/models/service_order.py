from django.db import models
from backend.apps.core.models.abstractions import TenantOwnedModel, BaseModel
from django.core.exceptions import ValidationError
from django.utils import timezone

class ServiceOrder(TenantOwnedModel):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("finished", "Finished"),
        ("awaiting_validation", "Awaiting Validation"),
        ("approved", "Approved/Closed"),
    ]

    identifier = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT, related_name="created_orders")
    assigned_to = models.ForeignKey("core.Technician", on_delete=models.PROTECT, related_name="assigned_orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="open")

    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.SET_NULL)
    client_name = models.CharField(max_length=200, blank=True)  # Nome livre preenchido na hora
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=30, blank=True)

    # Auto-tracking for audit (optional)
    status_history = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]

    def can_transition(self, user, new_status):
        """
        Verifica se a transição de status é válida de acordo com o workflow configurado do tenant
        e as permissões do usuário (nível).
        """
        from backend.apps.core.workflow import get_workflow_for_tenant, has_permission_for_status

        workflow = get_workflow_for_tenant(self.tenant)

        current = self.status
        if not any(t["from"] == current and t["to"] == new_status for t in workflow["transitions"]):
            return False

        return has_permission_for_status(user, new_status, workflow)

    def update_status(self, user, new_status):
        """
        Atualiza o status da ordem de serviço com validação do fluxo de trabalho.
        """
        if not self.can_transition(user, new_status):
            raise ValidationError(f"Transition from '{self.status}' to '{new_status}' not allowed.")

        self.status = new_status
        self.status_history.append({
            "from": self.status,
            "to": new_status,
            "changed_by": str(user),
            "timestamp": timezone.now().isoformat()
        })
        self.save()

    def __str__(self):
        return f"Service Order #{self.identifier} - {self.status.replace('_', ' ').title()}"

'''  ESTE MODEL <ServiceOrderDocument> SERÁ REMOVIDO EM ATUALIZAÇÕES FUTURAS PELO SEGUINTE MOTIVO:
        - ECONOMIA NO BANCO DE DADOS
        Percebi que salvar documentos que serão gerados dinamicamente de acordo com a ordem de serviço fabricada
        (que é suficientemente modular em seus dados e integrada com o banco de dados) além de ser pesado em médio prazo (e aqui se)
        considere uma economia motivada não pelo quesito custo de investimento (ou ao menos não só esse custo) mas pela falta de
        necessidade real de investir em salvar esses dados.

        O meu objetivo é salvar a informação de ordem de serviço, as imagens a ela atribuidas, assinaturas, listas, e dinamicamente gerar
        quando solicitado um pdf com as informações solicitadas, não sendo necessário salvar isso no banco de dados.
                  '''
class ServiceOrderDocument(BaseModel):

    service_order = models.OneToOneField("ServiceOrder", on_delete=models.CASCADE, related_name="pdf_document")
    file = models.FileField(upload_to="service_orders/pdfs/")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey("core.Technician", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Service Order PDF #{self.service_order.id}"