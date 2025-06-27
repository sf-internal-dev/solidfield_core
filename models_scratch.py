# from django.db import models
# from django.core.exceptions import ValidationError
# from datetime import timezone
# from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

# """ Abstrações de Modelo """ 
# class BaseModel(models.Model):
#     created_at = models.DateTimeField(default=timezone.now, editable=False)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         abstract = True


# class TenantOwnedModel(BaseModel):
#     tenant = models.ForeignKey("CompanyTenant", on_delete=models.PROTECT)
#     class Meta:
#         abstract = True


# class SoftDeletableModel(models.Model):
#     is_active = models.BooleanField(default=True)
#     class Meta:
#         abstract = True 


# class AccountHolderUser(AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(unique=True)
#     full_name = models.CharField(max_length=150)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)  # para login no admin

#     # Dados administrativos
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     # Relacionamento com tenant (opcional: pode criar várias ou só uma)
#     tenant = models.OneToOneField("CompanyTenant", on_delete=models.SET_NULL, null=True, blank=True)

#     USERNAME_FIELD = "email"

#     def __str__(self):
#         return self.email

# class CompanyTenant(models.Model):
#     name = models.CharField(max_length=150)
#     slug = models.SlugField(unique=True)  # Ex: "solidfield", usado para rotas ou identificação interna
#     is_active = models.BooleanField(default=True)
    
#     # Dados do responsável principal (para comunicação ou gestão)
#     primary_contact_name = models.CharField(max_length=100, blank=True)
#     primary_contact_email = models.EmailField(blank=True)
#     primary_contact_phone = models.CharField(max_length=30, blank=True)

#     # Dados administrativos
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     billing_account_id = models.CharField(max_length=100, blank=True, null=True)  # futuro: vincular com Stripe, etc.

#     owner = models.OneToOneField(
#         "AccountHolderUser",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="owned_tenant"
#     )

#     # Configurações gerais opcionais
#     locale = models.CharField(max_length=10, default="en-US")
#     timezone = models.CharField(max_length=50, default="America/Los_Angeles")

#     # Identidade visual (opcional)
#     logo = models.ImageField(upload_to="tenant_logos/", null=True, blank=True)
#     color_primary = models.CharField(max_length=7, default="#000000")  # Cor base da marca

#     class Meta:
#         verbose_name = "Company / Tenant"
#         verbose_name_plural = "Companies / Tenants"

#     def __str__(self):
#         return self.name

# """ """
# class Technician(TenantOwnedModel, SoftDeletableModel):
#     username = models.CharField(max_length=12)
#     social_name = models.CharField(max_length=150)
#     technician_permission = models.ForeignKey("PermissionLevel", on_delete=models.PROTECT)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.social_name

# class PermissionLevel(models.TextChoices):
#     L1 = "L1", "Field Level"
#     L2 = "L2", "Local Control"
#     L3 = "L3", "Operational Management"

# class PermissionFlag(BaseModel):
#     level = models.CharField(max_length=2, choices=PermissionLevel.choices)
#     action = models.CharField(max_length=100) 
#     allowed = models.BooleanField(default=False)

#     class Meta:
#         unique_together = ("tenant", "level", "action")

# class TemporaryDelegation(TenantOwnedModel, BaseModel):
#     from_user = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='delegations_given')
#     to_user = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='delegations_received')
#     valid_from = models.DateTimeField()
#     valid_until = models.DateTimeField()

#     def is_active(self):
#         now = timezone.now()
#         return self.valid_from <= now <= self.valid_until

# class DelegatedAction(BaseModel):
#     delegation = models.ForeignKey(
#         TemporaryDelegation, 
#         on_delete=models.CASCADE, 
#         related_name="actions"
#         )
#     action = models.CharField(max_length=100)

#     def __str__(self):
#         return f"{self.delegation} → {self.action}"
# """ """

# class ChecklistTemplate(TenantOwnedModel, SoftDeletableModel):
#     name = models.CharField(max_length=150)  # Ex: "Installing Standard Camera"
#     version = models.PositiveIntegerField(default=1)
#     created_by = models.ForeignKey(Technician, on_delete=models.PROTECT)
#     created_at = models.DateTimeField(auto_now_add=True)
#     service_type = models.CharField(max_length=100)  # Ex: "Installing", "Maintenance"
#     is_active = models.BooleanField(default=True)

#     class Meta:
#         unique_together = ("tenant", "name", "version")


# class ChecklistItemTemplate(BaseModel):
#     template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name="itens")
#     order = models.PositiveIntegerField()
#     question = models.CharField(max_length=300)

#     FIELD_TYPE = [
#         ("bool", "Yes/No"),
#         ("text", "Free Text"),
#         ("number", "General Number"),
#         ("choice", "Unique Selection"),
#         ("degree", "Angle (°)"),
#         ("length_cm", "Length (cm)"),
#         ("width_cm", "Width (cm)"),
#         ("height_cm", "Height (cm)"),
#         ("area_m2", "Area (m²)"),
#         ("voltage", "Voltage (V)"),
#         ("temperature", "Temperature (°C)"),
#         ("pressure", "Pressure (psi/bar)"),
#     ]
#     answer_type = models.CharField(max_length=20, choices=FIELD_TYPE)
#     required = models.BooleanField(default=True)
#     choice_options = models.TextField(blank=True)

#     class Meta:
#         ordering = ["order"]


# class Checklist(BaseModel):
#     service_order = models.OneToOneField("ServiceOrder", on_delete=models.CASCADE)
#     template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT)
#     filled_by = models.ForeignKey("Technician", on_delete=models.PROTECT)
#     filled_at = models.DateTimeField(auto_now_add=True)


# class ChecklistItemAnswer(BaseModel):
#     checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="answers")
#     item_template = models.ForeignKey(ChecklistItemTemplate, on_delete=models.PROTECT)

#     answer_bool = models.BooleanField(null=True, blank=True)
#     answer_texto = models.TextField(null=True, blank=True)
#     answer_number = models.FloatField(null=True, blank=True)
#     answer_choice = models.CharField(max_length=100, null=True, blank=True)

#     note = models.TextField(blank=True)

#     class Meta:
#         unique_together = ("checklist", "item_template")

#     def clean(self):
#         type = self.item_template.answer_type

#         if type != "bool":
#             self.answer_bool = None
#         if type != "text":
#             self.answer_texto = None
#         if type != "number":
#             self.answer_number = None
#         if type != "choice":
#             self.answer_choice = None

#         if type == "bool" and self.answer_bool is None:
#             raise ValidationError("Answer needs to be Yes or No.")
#         if type == "text" and not self.answer_texto:
#             raise ValidationError("Text is Required.")
#         if type == "choice" and not self.answer_choice:
#             raise ValidationError("Choice is Required.")
        
#         NUMERIC_TYPES = ["number", "degree", "length_cm", "width_cm", "height_cm", 
#                          "area_m2", "voltage", "temperature", "pressure"]

#         if type in NUMERIC_TYPES:
#             if self.answer_number is None and self.item_template.required:
#                 raise ValidationError(f"Numeric answer required for field type '{type}'.")
#         else:
#             self.answer_number = None

# class OfflineSyncQueue(BaseModel):
#     technician = models.ForeignKey(Technician, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     synced_at = models.DateTimeField(null=True, blank=True)
#     status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("conflict", "Conflict"), ("success", "Success")])
#     payload = models.JSONField()

# class AuditLog(BaseModel, TenantOwnedModel):
#     user = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True)
#     action = models.CharField(max_length=150)  # Ex: "status_update", "photo_upload"
#     reference_id = models.CharField(max_length=100)  # Pode ser ID da OS, checklist, etc
#     data = models.JSONField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

# class ServiceOrderPhoto(BaseModel):
#     service_order = models.ForeignKey("ServiceOrder", on_delete=models.CASCADE, related_name="photos")
#     uploaded_by = models.ForeignKey("Technician", on_delete=models.PROTECT)
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     # Uploaded image
#     image = models.ImageField(upload_to="service_photos/")

#     # Context/type of photo
#     PHOTO_TYPE_CHOICES = [
#         ("before", "Before Execution"),
#         ("after", "After Execution"),
#         ("issue", "Issue/Failure Identified"),
#         ("proof", "Proof of Service"),
#         ("custom", "Custom"),
#     ]
#     photo_type = models.CharField(max_length=20, choices=PHOTO_TYPE_CHOICES)

#     # Optional description
#     description = models.TextField(blank=True)

#     # Metadata
#     gps_latitude = models.FloatField(null=True, blank=True)
#     gps_longitude = models.FloatField(null=True, blank=True)
#     device_info = models.CharField(max_length=100, blank=True)

#     # Optional customer signature
#     customer_signed = models.BooleanField(default=False)
#     signature_image = models.ImageField(upload_to="signatures/", null=True, blank=True)

#     class Meta:
#         ordering = ["uploaded_at"]


# class ServiceOrder(TenantOwnedModel):
#     STATUS_CHOICES = [
#         ("open", "Open"),
#         ("in_progress", "In Progress"),
#         ("finished", "Finished"),
#         ("awaiting_validation", "Awaiting Validation"),
#         ("approved", "Approved/Closed"),
#     ]

#     identifier = models.CharField(max_length=50, unique=True)
#     created_by = models.ForeignKey("Technician", on_delete=models.PROTECT, related_name="created_orders")
#     assigned_to = models.ForeignKey("Technician", on_delete=models.PROTECT, related_name="assigned_orders")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="open")

#     client = models.ForeignKey("Client", null=True, blank=True, on_delete=models.SET_NULL)
#     client_name = models.CharField(max_length=200, blank=True)  # Nome livre preenchido na hora
#     client_email = models.EmailField(blank=True)
#     client_phone = models.CharField(max_length=30, blank=True)

#     # Auto-tracking for audit (optional)
#     status_history = models.JSONField(default=list)

#     class Meta:
#         ordering = ["-created_at"]

#     def can_transition(self, user, new_status):
#         """
#         Verifica se a transição de status é válida de acordo com o workflow configurado do tenant
#         e as permissões do usuário (nível).
#         """
#         from .workflow import get_workflow_for_tenant, has_permission_for_status

#         workflow = get_workflow_for_tenant(self.tenant)

#         current = self.status
#         if not any(t["from"] == current and t["to"] == new_status for t in workflow["transitions"]):
#             return False

#         return has_permission_for_status(user, new_status, workflow)

#     def update_status(self, user, new_status):
#         """
#         Atualiza o status da ordem de serviço com validação do fluxo de trabalho.
#         """
#         if not self.can_transition(user, new_status):
#             raise ValidationError(f"Transition from '{self.status}' to '{new_status}' not allowed.")

#         self.status = new_status
#         self.status_history.append({
#             "from": self.status,
#             "to": new_status,
#             "changed_by": str(user),
#             "timestamp": timezone.now().isoformat()
#         })
#         self.save()

# class ServiceOrderDocument(BaseModel):
#     service_order = models.OneToOneField("ServiceOrder", on_delete=models.CASCADE, related_name="pdf_document")
#     file = models.FileField(upload_to="service_orders/pdfs/")
#     generated_at = models.DateTimeField(auto_now_add=True)
#     generated_by = models.ForeignKey("Technician", null=True, blank=True, on_delete=models.SET_NULL)

#     def __str__(self):
#         return f"Service Order PDF #{self.service_order.id}"
    
# class TenantWorkflow(TenantOwnedModel):
#     workflow_json = models.JSONField()
#     updated_at = models.DateTimeField(auto_now=True)

# class Client(TenantOwnedModel, SoftDeletableModel):
#     PERSON_TYPE_CHOICES = [
#         ("individual", "Individual"),
#         ("company", "Company"),
#     ]

#     person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES, blank=True)

#     name = models.CharField(max_length=200) 
#     document_id = models.CharField(max_length=30, blank=True) 
#     contact_name = models.CharField(max_length=100, blank=True) 
#     phone = models.CharField(max_length=30, blank=True)
#     email = models.EmailField(blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ["name"]
#         unique_together = ("tenant", "document_id")

#     def __str__(self):
#         return self.name
    
# class ClientAddress(BaseModel):
#     client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="addresses")

#     label = models.CharField(max_length=100, help_text="Ex: Matriz, Filial Zona Norte, Residência")
#     street = models.CharField(max_length=200)
#     number = models.CharField(max_length=20)
#     complement = models.CharField(max_length=100, blank=True)
#     neighborhood = models.CharField(max_length=100)
#     city = models.CharField(max_length=100)
#     state = models.CharField(max_length=50)
#     zip_code = models.CharField(max_length=20)

#     gps_latitude = models.FloatField(null=True, blank=True)
#     gps_longitude = models.FloatField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.label} - {self.city}"

# class ClientFeedback(BaseModel):
#     service_order = models.OneToOneField(ServiceOrder, on_delete=models.CASCADE)

#     client = models.ForeignKey("Client", null=True, blank=True, on_delete=models.SET_NULL)

#     client_name = models.CharField(max_length=200, blank=True)
#     client_email = models.EmailField(blank=True)

#     stars = models.PositiveIntegerField()
#     comment = models.TextField(blank=True)
#     strengths = models.TextField(blank=True)
#     submitted_at = models.DateTimeField(auto_now_add=True)

# import secrets

# class FeedbackLink(BaseModel):
#     service_order = models.OneToOneField(ServiceOrder, on_delete=models.CASCADE)
#     key = models.CharField(max_length=20, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     used = models.BooleanField(default=False)

#     def save(self, *args, **kwargs):
#         if not self.key:
#             self.key = secrets.token_urlsafe(12)[:20]
#         super().save(*args, **kwargs)
