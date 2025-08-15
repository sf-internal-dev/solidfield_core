from backend.apps.checklist.utils.checklist_template_util import unit_for_item, has_unique_order_within_template, next_order_for_template
from backend.apps.checklist.models.checklist import ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.models.technician import TechniciansAggroupment, Technician
from typing import List, Tuple, Optional
from django.db.models import Max
from django.db import transaction


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



@transaction.atomic
def delegate_checklist_template_to_aggroupment(template: ChecklistTemplate, 
    aggroupment: TechniciansAggroupment,) -> Tuple[Optional[ChecklistTemplate], List[str]]:

    errors: List[str] = []

    if template.is_global:
        template.is_global = False
        template.save(update_fields=["is_global"])
        template.aggroupments.set([aggroupment])
        return template, errors

    template.aggroupments.add(aggroupment)
    return template, errors

@transaction.atomic
def remove_aggroupment_from_template(template: ChecklistTemplate,
    aggroupment: TechniciansAggroupment,) -> Tuple[Optional[ChecklistTemplate], List[str]]:

    errors: List[str] = []

    if template.is_global:
        return template, errors

    if template.aggroupments.count() <= 1 and template.aggroupments.filter(id=aggroupment.id).exists():
        return None, ["would_violate_min_groups"]
    

    template.aggroupments.remove(aggroupment)
    return template, errors


@transaction.atomic
def update_checklist_template_version(template: ChecklistTemplate, deactivate_previous: bool = True, copy_items: bool = True,
    copy_aggroupments: bool = True,) -> Tuple[Optional[ChecklistTemplate], List[str]]:

    errors: List[str] = []

    next_version = (
        ChecklistTemplate.objects
        .filter(tenant=template.tenant, name=template.name)
        .aggregate(m=Max("version"))
        .get("m") or 0
    ) + 1

    new_tpl = create_checklist_template(
        name=template.name,
        technician=template.created_by,
        service_type=template.service_type,
        is_global=template.is_global,
    )

    new_tpl.version = next_version
    new_tpl.is_active = True
    new_tpl.save(update_fields=["version", "is_active"])

    if copy_aggroupments and not new_tpl.is_global:
        ags = list(template.aggroupments.all())
        if ags:
            new_tpl.aggroupments.set(ags)

    if copy_items:
        ChecklistItemTemplate.objects.bulk_create([
            ChecklistItemTemplate(
                template=new_tpl,
                order=it.order,
                question=it.question,
                answer_type=it.answer_type,
                required=it.required,
                choice_options=it.choice_options or "",
            )
            for it in template.itens.all().order_by("order")
        ])

    if deactivate_previous and template.is_active:
        template.is_active = False
        template.save(update_fields=["is_active"])

    return new_tpl, errors