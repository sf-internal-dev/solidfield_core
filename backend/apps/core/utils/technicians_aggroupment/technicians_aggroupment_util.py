from typing import Tuple

def check_reached_aggroupment_limit(last_aggroupment_tag: str) -> bool:
    if last_aggroupment_tag != None:
        return True if last_aggroupment_tag == "D" else False
    return False

def define_aggroupment_tag(company_last_aggroupment):
    if check_reached_aggroupment_limit(company_last_aggroupment):
        pass
    if company_last_aggroupment == None:
        return "A"
    if company_last_aggroupment == "A":
        return "B"
    if company_last_aggroupment == "B":
        return "C"
    if company_last_aggroupment == "C":
        return "D"

def allowed_aggroupment(members_count: int) -> bool:
    return True if members_count >= 2 else False

def can_add_technician_to_aggroupment(technician, target_aggroupment) -> Tuple[bool, str]:

    if technician.tenant_id != target_aggroupment.tenant_id:
        return False, "Technician does not belong to the same tenant."

    if technician.aggroupment and technician.aggroupment_id != target_aggroupment.id:
        return False, f"Technician is already part of another aggroupment: {technician.aggroupment.tag}."
    
    return True, ""
