import re
from django.core.exceptions import ValidationError

def validate_tenant_core(value):
    if not re.match(r'^[A-Z0-9]{3,10}$', value):
        raise ValidationError("Code must have only capital letters and numbers.")