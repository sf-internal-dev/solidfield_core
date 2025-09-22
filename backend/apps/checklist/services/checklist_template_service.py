from backend.apps.checklist.utils.checklist_template_util import has_unique_order_within_template, next_order_for_template
from backend.apps.checklist.models.checklist import ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.models.technician import TechniciansAggroupment, Technician
from typing import Optional, List, Tuple, Iterable, Dict, Any
from django.db.models import Max
from django.db import transaction, IntegrityError
from backend.apps.core.services.technician_permission_service import has_permission
# -> Creates a new checklist template record with the given parameters
# Associates the template with the creating technician and service type
# Sets the global visibility flag as specified and returns the created object
def create_checklist_template(technician_operating: Technician, name: str, technician: Technician, service_type: str, is_global: bool):
    errors = []
    ok, perm_errors = has_permission(technician_operating, "create_checklist_template")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

    checklist_template = ChecklistTemplate.objects.create(
        name = name,
        created_by  = technician,
        service_type = service_type,
        is_global = is_global
    )

    return checklist_template, errors

# -> Adds a new item to a given checklist template
# Ensures order uniqueness within the template and assigns the next available order if not provided
# Creates the item with provided question, type, requirement flag, and choice options
# Returns the created item or validation errors if the order conflicts or constraints fail
def add_item_to_checklist_template(technician_operating: Technician, template: ChecklistTemplate, question: str, answer_type: str, 
    is_required: bool, choice_options: str, order: int = None) -> Tuple[ChecklistItemTemplate, List[str]]:
    
    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "add_item_to_checklist_template")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

    if order is None:
        order = next_order_for_template(template)

    temp_item = ChecklistItemTemplate(template=template, order=order)
    ok, err = has_unique_order_within_template(temp_item)
    if not ok:
        errors.extend(err)

    if errors:
        return None, errors

    try:
        item = ChecklistItemTemplate.objects.create(
            template=template,
            order=order,
            question=question,
            answer_type=answer_type,
            required=is_required,
            choice_options=choice_options or "",
        )
        return item, errors
    except IntegrityError:
        return None, [f"...:{order}"]

# -> Assigns a checklist template to a specific technician aggroupment
# Converts a global template into a group-specific one if necessary
# Adds the given aggroupment to the template and returns the updated object
@transaction.atomic
def delegate_checklist_template_to_aggroupment(technician_operating: Technician, template: ChecklistTemplate, 
    aggroupment: TechniciansAggroupment,) -> Tuple[Optional[ChecklistTemplate], List[str]]:


    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "delegate_checklist_template_to_aggroupment")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

    if template.is_global:
        template.is_global = False
        template.save(update_fields=["is_global"])
        template.aggroupments.set([aggroupment])
        return template, errors

    template.aggroupments.add(aggroupment)
    return template, errors

# -> Removes a technician aggroupment from a checklist template
# Prevents removal if the template is global or if it would leave the template with no groups
# Returns the updated template or an error if the removal would violate constraints
@transaction.atomic
def remove_aggroupment_from_template(technician_operating: Technician, template: ChecklistTemplate,
    aggroupment: TechniciansAggroupment,) -> Tuple[Optional[ChecklistTemplate], List[str]]:

    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "remove_aggroupment_from_template")
    if not ok:
        errors.extend(perm_errors)
        return None, errors
    
    if template.is_global:
        return template, errors

    if template.aggroupments.count() <= 1 and template.aggroupments.filter(id=aggroupment.id).exists():
        return None, ["would_violate_min_groups"]
    

    template.aggroupments.remove(aggroupment)
    return template, errors

# -> Creates a new version of a checklist template, optionally modifying its items
# Copies all items from the previous version, then removes and/or adds items as specified
# Optionally copies aggroupments and deactivates the previous template version
# Returns the new template version and any accumulated validation errors
@transaction.atomic
def update_checklist_template_version(technician_operating: Technician, template: ChecklistTemplate,*,orders_to_remove: Optional[Iterable[int]] = None, 
    items_to_add: Optional[Iterable[Dict[str, Any]]] = None,  copy_aggroupments: bool = True, deactivate_previous: bool = True,
    ) -> Tuple[Optional[ChecklistTemplate], List[str]]:

    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "update_checklist_template_version")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

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

    if orders_to_remove:
        for ord_ in orders_to_remove:
            obj = new_tpl.itens.filter(order=ord_).first()
            if not obj:
                errors.append(f"item_not_found_by_order:{ord_}")
                continue
            obj.delete()

    if items_to_add:
        for payload in items_to_add:
            item, errs = add_item_to_checklist_template(
                template=new_tpl,
                question=(payload.get("question") or "").strip(),
                answer_type=payload.get("answer_type"),
                is_required=bool(payload.get("is_required", True)),
                choice_options=payload.get("choice_options", "") or "",
                order=payload.get("order"),
            )
            errors.extend(errs)

    if deactivate_previous and template.is_active:
        template.is_active = False
        template.save(update_fields=["is_active"])

    return new_tpl, errors
