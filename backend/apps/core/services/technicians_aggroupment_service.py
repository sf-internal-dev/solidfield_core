from backend.apps.core.utils.technicians_aggroupment.technicians_aggroupment_util import define_aggroupment_tag, allowed_aggroupment,can_add_technician_to_aggroupment
from backend.apps.core.models import Technician, TechniciansAggroupment, CompanyTenant
from backend.apps.core.services.audition_log_service import log_group_assignment
from backend.apps.core.services.technician_permission_service import has_permission

def create_technicians_aggroupment(technician: Technician, tenant: CompanyTenant):
    ok, error = has_permission(technician=technician, action_code='create_technicians_aggroupment')
    if ok:
        last_aggroupment = tenant.techniciansaggroupments.order_by("-id").first()
        tag = define_aggroupment_tag(company_last_aggroupment=last_aggroupment)
        aggroupment = TechniciansAggroupment.objects.create(
            tenant=technician.tenant,
            tag=tag
        )
        
        return aggroupment, error
    return None, error

def add_technician_to_aggroupment(technician_operating: Technician, aggroupment: TechniciansAggroupment,technician_to_dd: Technician):
    ok_p, error_p = has_permission(technician=technician_operating, action_code='add_technician_to_aggroupment')
    if error_p is not "":
        return error_p
    ok, error = can_add_technician_to_aggroupment(technician=technician_to_dd, target_aggroupment=aggroupment)
    if ok and ok_p:
        log_group_assignment(technician=technician_to_dd,technicians=aggroupment.members.username,aggroupment_tag=aggroupment.tag)
        return technician_to_dd.aggroupment == aggroupment
    return error

def check_aggroupment_is_allowed_to_operate(technician_operating: Technician, aggroupment: TechniciansAggroupment):
    ok, error = has_permission(technician=technician_operating, action_code='check_aggroupment_is_allowed_to_operate')
    if ok:
        count = aggroupment.members.count()
        if allowed_aggroupment(count):
            return aggroupment.allowed_to_operate == True
    return error