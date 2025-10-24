from backend.apps.core.utils.tenant.tenant_slug_util import sanitize_tenant_slug, suggest_company_slug
from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_code_attempts
from backend.apps.core.validators.tenant_validator import validate_tenant_name, validate_hex_color, validate_optional_email, validate_optional_phone, validate_slug_format
from django.utils.crypto import get_random_string
from backend.apps.core.models.tenant import CompanyTenant, TenantStatusWorkflow
from backend.apps.core.models.user import AccountHolderUser
from backend.apps.core.services.status_workflow_service import create_custom_status_workflow, check_if_custom_status_workflow
from typing import Union, IO, Optional, Tuple, List
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File, ContentFile
from django.db.models.fields.files import ImageFieldFile
# -> Resolves a unique slug based on the company name
# Tries cleaned username-style suggestions and checks availability
# If all are taken, falls back to a numeric suffix strategy
def resolve_available_slug_from_name(company_name: str) -> Tuple[Optional[str], str]:

    suggestions = suggest_company_slug(company_name)

    for suggestion in suggestions:
        if not CompanyTenant.objects.filter(slug=suggestion).exists():
            return suggestion, ""

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
    for attempt in generate_tenant_code_attempts(slug):
        if not CompanyTenant.objects.filter(tenant_code=attempt).exists():
            return attempt

    base = generate_tenant_code_attempts(slug)[0][:4]
    suffix = get_random_string(2).upper()
    return f"{base}{suffix}"

# -> Prepares both slug and tenant_code for a new CompanyTenant
# Ensures both values are unique and derived from the company name
def prepare_company_slug_and_code(company_name: str) -> dict:
    slug, err = resolve_available_slug_from_name(company_name)
    code = generate_valid_tenant_code(slug) if slug else ""

    return {
        "slug": slug,
        "tenant_code": code
    }

def register_tenant(name: str, slug: str, tenant_code: str,
    billing_account_id: str, owner: AccountHolderUser, locale: str, timezone: str):

    errors = []
    primary_contact_name  = owner.full_name
    primary_contact_email = owner.email
    primary_contact_phone = getattr(owner, "phone", None) or None

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
        billing_account_id = billing_account_id,
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

def register_tenant_branding(tenant: CompanyTenant, color_primary: str, logo: ImageInput | None = None):
    errors = []

    if not validate_hex_color(value=color_primary):
        errors.append("invalid_hex_color")

    if errors:
        return None, errors
    
    tenant.color_primary = color_primary

    # precisa validar logo!
    # if not validate_logo(value=logo):
    #     errors.append("invalid_logo)
    tenant.logo = logo
    tenant.save()
    
    return tenant, errors

# -> Updates an existing tenant's information
# Validates all provided fields and updates only the ones that are valid
# Returns the updated tenant or None with error messages
def update_tenant(tenant_id: int, **update_data) -> Tuple[Optional[CompanyTenant], List[str]]:
    errors = []
    
    try:
        tenant = CompanyTenant.objects.get(id=tenant_id)
    except CompanyTenant.DoesNotExist:
        return None, ["tenant_not_found"]
    
    # Validate and update fields
    if "name" in update_data:
        if validate_tenant_name(update_data["name"]):
            tenant.name = update_data["name"]
        else:
            errors.append("invalid_tenant_name")
    
    if "slug" in update_data:
        if validate_slug_format(update_data["slug"]):
            # Check if slug is unique
            if CompanyTenant.objects.filter(slug=update_data["slug"]).exclude(id=tenant_id).exists():
                errors.append("slug_already_exists")
            else:
                tenant.slug = update_data["slug"]
        else:
            errors.append("invalid_slug_format")
    
    if "primary_contact_name" in update_data:
        tenant.primary_contact_name = update_data["primary_contact_name"]
    
    if "primary_contact_email" in update_data:
        if validate_optional_email(update_data["primary_contact_email"]):
            tenant.primary_contact_email = update_data["primary_contact_email"]
        else:
            errors.append("invalid_email")
    
    if "primary_contact_phone" in update_data:
        if validate_optional_phone(update_data["primary_contact_phone"]):
            tenant.primary_contact_phone = update_data["primary_contact_phone"]
        else:
            errors.append("invalid_phone_number")
    
    if "billing_account_id" in update_data:
        tenant.billing_account_id = update_data["billing_account_id"]
    
    if "country" in update_data:
        tenant.country = update_data["country"]
    
    if "locale" in update_data:
        tenant.locale = update_data["locale"]
    
    if "timezone" in update_data:
        tenant.timezone = update_data["timezone"]
    
    if "color_primary" in update_data:
        if validate_hex_color(update_data["color_primary"]):
            tenant.color_primary = update_data["color_primary"]
        else:
            errors.append("invalid_hex_color")
    
    if "logo" in update_data:
        tenant.logo = update_data["logo"]
    
    if "is_active" in update_data:
        tenant.is_active = update_data["is_active"]
    
    if errors:
        return None, errors
    
    tenant.save()
    return tenant, errors

# -> Gets the current workflow configuration for a tenant
# Returns the workflow as a labeled structure or None if not found
def get_tenant_workflow(tenant_id: int) -> Tuple[Optional[dict], List[str]]:
    try:
        tenant = CompanyTenant.objects.get(id=tenant_id)
    except CompanyTenant.DoesNotExist:
        return None, ["tenant_not_found"]
    
    # Check if tenant has a custom workflow
    workflow, errors = check_if_custom_status_workflow(tenant.id)
    
    if errors:
        return None, errors
    
    return workflow, []

# -> Updates the workflow configuration for a tenant
# Validates the workflow structure before saving
# Returns success status and error messages
def update_tenant_workflow(tenant_id: int, workflow_data: dict) -> Tuple[bool, List[str]]:
    try:
        tenant = CompanyTenant.objects.get(id=tenant_id)
    except CompanyTenant.DoesNotExist:
        return False, ["tenant_not_found"]
    
    # Create or update the workflow
    success, errors = create_custom_status_workflow(tenant, workflow_data)
    
    return success, errors