from django.db import models
from backend.apps.core.models.abstractions import TenantOwnedModel, SoftDeletableModel, BaseModel

class Client(TenantOwnedModel, SoftDeletableModel):
    PERSON_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("company", "Company"),
    ]

    person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES, blank=True)

    name = models.CharField(max_length=200) 
    document_id = models.CharField(max_length=30, blank=True) 
    contact_name = models.CharField(max_length=100, blank=True) 
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("tenant", "document_id")

    def __str__(self):
        return self.name
    
class ClientAddress(BaseModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="addresses")

    label = models.CharField(max_length=100, help_text="Ex: Matriz, Filial Zona Norte, Residência")
    street = models.CharField(max_length=200)
    number = models.CharField(max_length=20)
    complement = models.CharField(max_length=100, blank=True)
    neighborhood = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)

    gps_latitude = models.FloatField(null=True, blank=True)
    gps_longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        parts = [
            self.label,
            f"{self.street}, {self.number}",
            self.complement if self.complement else "",
            self.neighborhood,
            f"{self.city} - {self.state}",
            self.zip_code
        ]
        return ", ".join(filter(None, parts))