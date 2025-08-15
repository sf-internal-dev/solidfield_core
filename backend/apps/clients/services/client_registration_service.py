from backend.apps.clients.utils.client.client_address_util import validate_postal_code, validate_region_code,validate_coordinates
from backend.apps.clients.utils.client.client_registration_util import validate_document_id,validate_phone_number
from backend.apps.clients.models.client import Client, ClientAddress
from typing import Tuple, List, Optional

def register_client_document_and_phone(client: Client, document_id:str, phone_number: str, country:str) -> Tuple[Client, List[str]]:
    errors = []
    
    if validate_document_id(document_id, country):
        client.document_id = document_id
        client.save(update_fields=["document_id"])
    else:
        errors.append("invalid_document_id")

    if validate_phone_number(phone_number=phone_number, country=country):
        client.phone = phone_number
        client.save(update_fields=["phone"])
    else:
        errors.append("invalid_phone_number")

    return client, errors

def register_client_address(client: Client, code: str, state: str, country: str, lat: float,
        lng: float, label: str = None, street: str = None, number: str = None, 
        complement: str = None, neighborhood: str = None, city: str = None) -> Tuple[Optional[ClientAddress], List[str]]:
    
    errors = []

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
        zip_code=code,
        gps_latitude=lat,
        gps_longitude=lng
    )

    return address, errors
