from backend.apps.clients.utils.client.client_address_util import (validate_postal_code, validate_region_code, 
                                                                   validate_coordinates, validate_address_fields,
                                                                   format_full_address,
                                                                   )
from backend.apps.clients.utils.client.client_registration_util import validate_document_id,validate_phone_number
from backend.apps.clients.models.client import Client, ClientAddress

def register_client_document_and_phone(client: Client, document_id:str, phone_number: str, country:str):
    if validate_document_id(document_id,country):
        client.document_id = document_id
        client.save()
    if validate_phone_number(phone_number=phone_number, country=country):
        client.phone = phone_number
        client.save()

    return client

def register_client_address(client: Client, code: str, state: str, country: str, lat: float,
                            lng: float, label: str = None, street: str = None, number: str = None, 
                            complement: str = None, neighborhood: str = None, city: str = None):
    if (
        validate_postal_code(code=code, country=country)
        and validate_region_code(state=state, country=country)
        and validate_coordinates(lat=lat, lng=lng)
    ):
        return ClientAddress.objects.create(
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
