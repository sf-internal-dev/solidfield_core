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

class ChecklistItemTemplateInline(admin.TabularInline):
    model = ChecklistItemTemplate
    extra = 1
    ordering = ("order",)



@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    inlines = [ChecklistItemTemplateInline]
    list_display = ("name", "version", "created_by", "created_at", "service_type", "is_active")
    search_fields = ("name", "service_type", "created_by__social_name")
    list_filter = ("is_active", "service_type", "created_at")
    ordering = ("-created_at",)

