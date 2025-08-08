from backend.apps.core.utils.technicians_aggroupment.technicians_aggroupment_util import define_aggroupment_tag, allowed_aggroupment,can_add_technician_to_aggroupment
from backend.apps.core.models import Technician, TechniciansAggroupment, CompanyTenant

def create_technicians_aggroupment(tenant: CompanyTenant):
    last_aggroupment = tenant.techniciansaggroupments.order_by("-id").first()
    return define_aggroupment_tag(company_last_aggroupment=last_aggroupment)

def add_technician_to_aggroupment(aggroupment: TechniciansAggroupment,technician: Technician):
    can_add, error = can_add_technician_to_aggroupment(technician=technician, target_aggroupment=aggroupment)
    if can_add:
        return technician.aggroupment == aggroupment
    return error

def check_aggroupment_is_allowed_to_operate(aggroupment):
    count = aggroupment.members.count()
    if allowed_aggroupment(count):
        return aggroupment.allowed_to_operate == True
