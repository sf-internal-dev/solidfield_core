from backend.apps.core.utils.technicians_aggroupment.technicians_aggroupment_util import define_aggroupment_tag, allowed_aggroupment,can_add_technician_to_aggroupment
from backend.apps.core.models import Technician, TechniciansAggroupment, CompanyTenant
from backend.apps.core.services.audition_log_service import log_group_assignment
from backend.apps.core.services.technician_permission_service import has_permission

def create_technicians_aggroupment(technician: Technician, tenant: CompanyTenant):
    ok, error = has_permission(technician=technician, action_code='create_technicians_aggroupment')
    if ok:
        last_aggroupment = tenant.techniciansaggroupments.order_by("-id").first()
        return define_aggroupment_tag(company_last_aggroupment=last_aggroupment)
    return error

def add_technician_to_aggroupment(aggroupment: TechniciansAggroupment,technician: Technician):
    can_add, error = can_add_technician_to_aggroupment(technician=technician, target_aggroupment=aggroupment)
    if can_add:
        log_group_assignment(technician=technician,technicians=aggroupment.members.username,aggroupment_tag=aggroupment.tag)
        return technician.aggroupment == aggroupment
    return error

def check_aggroupment_is_allowed_to_operate(aggroupment):
    count = aggroupment.members.count()
    if allowed_aggroupment(count):
        return aggroupment.allowed_to_operate == True
