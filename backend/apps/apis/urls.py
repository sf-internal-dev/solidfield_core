from backend.apps.core.api import audition_log_api, tenant_api, technician_api
from backend.apps.checklist.api import checklist_api, checklist_template_api
from backend.apps.clients.api import client_api, client_feedback_api
from backend.apps.orders.api import work_order_api
from rest_framework.routers import DefaultRouter

from django.urls import path, include

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path('register_technician_api/',technician_api.register_technician_api, name="register_technician_api"),
    path("register_tenant_api/",tenant_api.register_tenant_api, name="register_tenant_api"),
    path("register_tenant_branding_api/",tenant_api.register_tenant_branding_api, name="register_tenant_branding_api"),
    path("create_checklist_api/",checklist_api.create_checklist_api, name="create_checklist_api"),
    path("create_checklist_item_answer_api/",checklist_api.create_checklist_item_answer_api, name="create_checklist_item_answer_api"),
    path("create_checklist_template_api/",checklist_template_api.create_checklist_template_api, name="create_checklist_template_api"),
    path("create_checklist_item_template_api/",checklist_template_api.create_checklist_item_template_api, name="create_checklist_item_template_api"),
]
