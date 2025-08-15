from backend.apps.checklist.utils.checklist_template_util import unit_for_item, has_unique_order_within_template, next_order_for_template
from backend.apps.checklist.models.checklist import ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.models.technician import TechniciansAggroupment, Technician
from typing import List, Tuple


def create_checklist_template(name: str, technician: Technician, service_type: str, is_global: bool):
    checklist_template = ChecklistTemplate.objects.create(
        name = name,
        created_by  = technician,
        service_type = service_type,
        is_global = is_global
    )

    return checklist_template

def add_item_to_checklist_template(template: ChecklistTemplate, question: str, answer_type: str, 
    is_required: bool, choice_options: str, order: int = None) -> Tuple[ChecklistItemTemplate, List[str]]:
    
    errors: List[str] = []

    if order is None:
        order = next_order_for_template(template)

    temp_item = ChecklistItemTemplate(template=template, order=order)
    ok, err = has_unique_order_within_template(temp_item)
    if not ok:
        errors.extend(err)

    if errors:
        return None, errors

    item = ChecklistItemTemplate.objects.create(
        template=template,
        order=order,
        question=question,
        answer_type=answer_type,
        required=is_required,
        choice_options=choice_options
    )

    return item, errors



def delegate_checklist_template_to_aggroupment():
    pass

def update_checklist_template_version():
    pass

