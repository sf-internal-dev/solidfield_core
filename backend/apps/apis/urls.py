from backend.apps.core.api import audition_log_api, tenant_api, technician_api
from backend.apps.checklist.api import checklist_api, checklist_template_api
from backend.apps.clients.api import client_api, client_feedback_api
from backend.apps.orders.api import work_order_api

from django.urls import path

urlpatterns = [
    path('register_technician_api/',technician_api.register_technician_api, name="register_technician_api")
]
