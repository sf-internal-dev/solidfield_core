import nested_admin
from django.contrib import admin
from backend.apps.checklist.models import Checklist, ChecklistItemAnswer, ChecklistItemTemplate, ChecklistTemplate

class ChecklistItemAnswerInline(nested_admin.NestedTabularInline):
    model = ChecklistItemAnswer
    extra = 0

class ChecklistInline(nested_admin.NestedStackedInline):
    model = Checklist
    inlines = [ChecklistItemAnswerInline]
    extra = 0

class ChecklistItemTemplateInline(nested_admin.NestedTabularInline):
    model = ChecklistItemTemplate
    extra = 1
    ordering = ("order",)


class ChecklistTemplateInline(nested_admin.NestedStackedInline):
    model = ChecklistTemplate
    inlines = [ChecklistItemTemplateInline]
    extra = 1

