from backend.apps.clients.utils.client.client_address_util import validate_postal_code, validate_region_code,validate_coordinates
from backend.apps.clients.utils.client.client_registration_util import (validate_document_id,validate_phone_number)
from backend.apps.clients.validators.client_validator import validate_email_field, validate_name, validate_contact_name
from backend.apps.clients.models.client import Client, ClientAddress
from backend.apps.core.models.technician import Technician
from typing import Tuple, List, Optional
from backend.apps.core.services.technician_permission_service import has_permission

# -> Registers a client's document ID and phone number with validation
# Validates the document ID and phone number based on the provided country
# Updates each field individually only if validation passes
# Appends error codes for any invalid fields without interrupting the process
# Always returns the updated client object along with the list of errors
from typing import Tuple, List, Optional

def create_or_update_client(
    technician_operating: Technician,
    client: Optional[Client] = None,
    *,
    person_type: Optional[str] = None,
    name: Optional[str] = None,
    document_id: Optional[str] = None,
    contact_name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    country: Optional[str] = None
) -> Tuple[Optional[Client], List[str]]:

    errors: List[str] = []

    # permission check
    ok, perm_errors = has_permission(technician_operating, "add_or_update_client")
    if not ok:
        return None, perm_errors

    if client is None:
        client = Client(tenant=technician_operating.tenant)

    # person_type
    if person_type:
        if person_type not in dict(Client.PERSON_TYPE_CHOICES):
            errors.append("invalid_person_type")
        else:
            client.person_type = person_type

    # name
    if name:
        valid, name_errors = validate_name(name)
        if valid:
            client.name = name
        else:
            errors.extend(name_errors)

    # document_id
    if document_id:
        if validate_document_id(document_id, country):
            client.document_id = document_id
        else:
            errors.append("invalid_document_id")

    # contact_name
    if contact_name:
        valid, contact_errors = validate_contact_name(contact_name)
        if valid:
            client.contact_name = contact_name
        else:
            errors.extend(contact_errors)

    # phone
    if phone:
        if validate_phone_number(phone, country):
            client.phone = phone
        else:
            errors.append("invalid_phone_number")

    # email
    if email:
        if validate_email_field(email):
            client.email = email
        else:
            errors.append("invalid_email")

    # save only if there are no critical errors
    if not errors:
        client.save()

    return client, errors

# -> Registers a new address for a given client after validating all components
# Validates postal code, region code, and geographic coordinates based on the country
# If any validation fails, returns None along with the corresponding error codes
# Creates and returns the address object if all validations pass
# Returns the created address and an empty error list upon success
def register_client_address(technician_operating: Technician, client: Client, code: str, state: str, country: str, lat: float,
        lng: float, label: str = None, street: str = None, number: str = None, 
        complement: str = None, neighborhood: str = None, city: str = None) -> Tuple[Optional[ClientAddress], List[str]]:
    
    errors = []
    ok, perm_errors = has_permission(technician_operating, "add_client_address")
    if not ok:
        return None, perm_errors

    if not validate_postal_code(code=code, country=country):
        errors.append("invalid_postal_code")
    if not validate_region_code(state=state, country=country):
        errors.append("invalid_region_code")
    if not validate_coordinates(lat=lat, lng=lng):
        errors.append("invalid_coordinates")

    if errors:
        return None, errors

    address = ClientAddress.objects.create(
        client=client,
        label=label,
        street=street or "",
        number=number,
        complement=complement,
        neighborhood=neighborhood,
        city=city or "",
        state=state,
        postal_code=code,
        gps_latitude=lat,
        gps_longitude=lng
    )

    return address, errors
