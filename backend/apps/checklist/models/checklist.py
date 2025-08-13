from backend.apps.core.models.abstractions import TenantOwnedModel, SoftDeletableModel, BaseModel
from backend.apps.core.models.technician import Technician, TechniciansAggroupment
from django.db import models
from django.core.exceptions import ValidationError

class ChecklistTemplate(TenantOwnedModel, SoftDeletableModel):
    name = models.CharField(max_length=150)  # Ex: "Installing Standard Camera"
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(Technician, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    service_type = models.CharField(max_length=100)  # Ex: "Installing", "Maintenance"
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(default=True)

    aggroupments = models.ManyToManyField(
        TechniciansAggroupment,
        related_name="checklist_templates",
        blank=True,
    )

    class Meta:
        unique_together = ("tenant", "name", "version")

    def __str__(self):
        return f"{self.name} v{self.version} ({self.service_type})"

    def clean(self):
        super().clean()

        # Se for global, não pode ter grupos
        if self.is_global:
            # Se ainda não está salvo, não sabemos o M2M; o form/serializer deve validar.
            if self.pk and self.aggroupments.exists():
                raise ValidationError("Templates globais não podem estar ligados a aggroupments.")
        else:
            # Se não for global, precisa de pelo menos 1 grupo (quando possível checar)
            if self.pk and not self.aggroupments.exists():
                raise ValidationError("Templates não globais precisam de ao menos um aggroupment.")

    def save(self, *args, **kwargs):
        # Se marcar como global, limpe os vínculos depois de salvar
        becoming_global = self.pk is not None and self.is_global
        super().save(*args, **kwargs)
        if becoming_global:
            # Garante regra mesmo em escrituras diretas
            self.aggroupments.clear()



class ChecklistItemTemplate(BaseModel):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name="itens")
    order = models.PositiveIntegerField()
    question = models.CharField(max_length=300)

    FIELD_TYPE = [
        # Boolean & Text
        ("bool", "Yes/No"),
        ("text", "Free Text"),
        # Numeric General
        ("number", "General Number"),
        ("choice", "Unique Selection"),

        # Angles
        ("degree", "Angle (°)"),

        # Metric Dimensions
        ("length_cm", "Length (cm)"),
        ("width_cm", "Width (cm)"),
        ("height_cm", "Height (cm)"),
        ("area_m2", "Area (m²)"),
        ("volume_l", "Volume (L)"),
        ("weight_kg", "Weight (kg)"),

        # Imperial Dimensions
        ("length_in", "Length (in)"),
        ("width_in", "Width (in)"),
        ("height_in", "Height (in)"),
        ("area_ft2", "Area (ft²)"),
        ("volume_gal", "Volume (gal)"),
        ("weight_lb", "Weight (lb)"),

        # Electrical & Energy
        ("voltage", "Voltage (V)"),
        ("current_amp", "Current (A)"),
        ("frequency_hz", "Frequency (Hz)"),
        ("power_w", "Power (W)"),
        ("power_kw", "Power (kW)"),
        # Environmental
        ("temperature", "Temperature (°C)"),
        ("temperature_f", "Temperature (°F)"),
        ("pressure", "Pressure (psi/bar)"),
        ("humidity_pct", "Humidity (%)"),
        ("speed_kmh", "Speed (km/h)"),
        ("speed_mph", "Speed (mph)"),
    ]

    answer_type = models.CharField(max_length=20, choices=FIELD_TYPE)
    required = models.BooleanField(default=True)
    choice_options = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]
    
    def __str__(self):
        return f"{self.order}. {self.question[:40]}{'...' if len(self.question) > 40 else ''}"



class Checklist(BaseModel):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT)
    filled_by = models.ForeignKey("core.Technician", on_delete=models.PROTECT)
    filled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checklist #{self.id} - OS {self.service_order.identifier}"


class ChecklistItemAnswer(BaseModel):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="answers")
    item_template = models.ForeignKey(ChecklistItemTemplate, on_delete=models.PROTECT)

    answer_bool = models.BooleanField(null=True, blank=True)
    answer_texto = models.TextField(null=True, blank=True)
    answer_number = models.FloatField(null=True, blank=True)
    answer_choice = models.CharField(max_length=100, null=True, blank=True)

    note = models.TextField(blank=True)

    class Meta:
        unique_together = ("checklist", "item_template")

    def clean(self):
        type = self.item_template.answer_type

        if type != "bool":
            self.answer_bool = None
        if type != "text":
            self.answer_texto = None
        if type != "number":
            self.answer_number = None
        if type != "choice":
            self.answer_choice = None

        if type == "bool" and self.answer_bool is None:
            raise ValidationError("Answer needs to be Yes or No.")
        if type == "text" and not self.answer_texto:
            raise ValidationError("Text is Required.")
        if type == "choice" and not self.answer_choice:
            raise ValidationError("Choice is Required.")
        
        NUMERIC_TYPES = ["number", "degree", "length_cm", "width_cm", "height_cm", 
                         "area_m2", "voltage", "temperature", "pressure"]

        if type in NUMERIC_TYPES:
            if self.answer_number is None and self.item_template.required:
                raise ValidationError(f"Numeric answer required for field type '{type}'.")
        else:
            self.answer_number = None

    def __str__(self):
        return f"{self.checklist.filled_by} Answer for '{self.item_template.question[:30]}...'"
