from backend.apps.core.utils.tenant.tenant_slug_util import sanitize_tenant_slug, suggest_company_slug
from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_identifier_code
from backend.apps.core.validators.tenant_validator import validate_tenant_name, validate_hex_color, validate_optional_email, validate_optional_phone, validate_slug_format

from core.models.tenant import CompanyTenant
from core.models.user import AccountHolderUser
from typing import Union, IO, Optional
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File, ContentFile
from django.db.models.fields.files import ImageFieldFile
# -> Resolves a unique slug based on the company name
# Tries cleaned username-style suggestions and checks availability
# If all are taken, falls back to a numeric suffix strategy
def resolve_available_slug_from_name(company_name: str) -> Optional[str]:
    suggestions = suggest_company_slug(company_name)

    for suggestion in suggestions:
        if not CompanyTenant.objects.filter(slug=suggestion).exists():
            return suggestion

    base_slug = sanitize_tenant_slug(company_name)
    if not base_slug:
        base_slug = "tenant"

    for i in range(1, 30):
        slug_attempt = f"{base_slug}{i}"
        if not CompanyTenant.objects.filter(slug=slug_attempt).exists():
            return slug_attempt, ""

    # Couldn't create a slug suggestion for your company. Please choose one manually."
    return None, "could_not_create_slug_suggestion."

# -> Generates a unique tenant_code based on the slug
# Iterates over identifier suggestions and checks availability
# If exhausted, falls back to a random suffix strategy
def generate_valid_tenant_code(slug: str) -> str:
    for attempt in generate_tenant_identifier_code(slug):
        if not CompanyTenant.objects.filter(tenant_code=attempt).exists():
            return attempt

    base = generate_tenant_identifier_code(slug)[0][:4]
    return f"{base}{generate_tenant_identifier_code(length=2).upper()}"


# -> Prepares both slug and tenant_code for a new CompanyTenant
# Ensures both values are unique and derived from the company name
def prepare_company_slug_and_code(company_name: str) -> dict:
    slug = resolve_available_slug_from_name(company_name)
    code = generate_valid_tenant_code(slug)

    return {
        "slug": slug,
        "tenant_code": code
    }

def register_tenant(name: str, slug: str, tenant_code: str,
    billind_account_id: str, owner: AccountHolderUser, locale: str, timezone: str):
    
    errors = []
    primary_contact_name  = owner.full_name
    primary_contact_email = owner.email
    primary_contact_phone = owner.phone

    if not validate_tenant_name(value=name):
        errors.append("invalid_tenant_name")
    if not validate_slug_format(value=slug):
        errors.append("invalid_slug_format")
    if not validate_optional_email(value=primary_contact_email):
        errors.append("invalid_slug_format")
    if not validate_optional_phone(value=primary_contact_phone):
        errors.append("invalid_slug_format")

    if errors:
        return None, errors
    
    tenant = CompanyTenant.objects.create(
        name = name,
        slug = slug,
        tenant_code = tenant_code,
        primary_contact_name = primary_contact_name,
        primary_contact_email = primary_contact_email,
        primary_contact_phone = primary_contact_phone,
        billind_account_id = billind_account_id,
        owner = owner,
        locale = locale,
        timezone = timezone
    )
    
    return tenant, errors


# Lê bytes (ex.: io.BytesIO)
BinaryReadable = IO[bytes]

ImageInput = Union[
    UploadedFile,     # vindo da request/form
    File, ContentFile, 
    ImageFieldFile,   # vindo de um model já salvo
    BinaryReadable,   # ex.: BytesIO
    bytes,            # bytes prontos
    str, Path,        # caminho no disco
]

def register_tenant_branding(color_primary: str, logo: ImageInput | None = None):
    pass