from backend.apps.core.api import audition_log_api, tenant_api, technician_api
from backend.apps.checklist.api import checklist_api, checklist_template_api
from backend.apps.clients.api import client_api, client_feedback_api
from backend.apps.orders.api import work_order_api
from rest_framework.routers import DefaultRouter

from django.urls import path, include

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    # Technician APIs
    path('register_technician_api/',technician_api.register_technician_api, name="register_technician_api"),
    path('update_technician_api/<int:technician_id>/',technician_api.update_technician_api, name="update_technician_api"),
    path('delete_technician_api/<int:technician_id>/',technician_api.delete_technician_api, name="delete_technician_api"),
    path('delegate_permissions_api/',technician_api.delegate_permissions_api, name="delegate_permissions_api"),
    path('get_technician_permissions_api/<int:technician_id>/',technician_api.get_technician_permissions_api, name="get_technician_permissions_api"),
    # Tenant APIs
    path("register_tenant_api/",tenant_api.register_tenant_api, name="register_tenant_api"),
    path("register_tenant_branding_api/",tenant_api.register_tenant_branding_api, name="register_tenant_branding_api"),
    path("update_tenant_api/<int:tenant_id>/",tenant_api.update_tenant_api, name="update_tenant_api"),
    path("get_tenant_workflow_api/<int:tenant_id>/",tenant_api.get_tenant_workflow_api, name="get_tenant_workflow_api"),
    path("update_tenant_workflow_api/<int:tenant_id>/",tenant_api.update_tenant_workflow_api, name="update_tenant_workflow_api"),
    # Checklist APIs
    path("create_checklist_api/",checklist_api.create_checklist_api, name="create_checklist_api"),
    path("create_checklist_item_answer_api/",checklist_api.create_checklist_item_answer_api, name="create_checklist_item_answer_api"),
    path("list_checklists_api/",checklist_api.list_checklists_api, name="list_checklists_api"),
    path("get_checklist_api/<int:checklist_id>/",checklist_api.get_checklist_api, name="get_checklist_api"),
    path("submit_checklist_api/<int:checklist_id>/",checklist_api.submit_checklist_api, name="submit_checklist_api"),
    path("get_checklist_progress_api/<int:checklist_id>/",checklist_api.get_checklist_progress_api, name="get_checklist_progress_api"),
    path("create_checklist_template_api/",checklist_template_api.create_checklist_template_api, name="create_checklist_template_api"),
    path("create_checklist_item_template_api/",checklist_template_api.create_checklist_item_template_api, name="create_checklist_item_template_api"),
    # Client APIs
    path("register_client_api/",client_api.register_client_api, name="register_client_api"),
    path("register_client_adress_api/", client_api.register_client_adress_api, name="register_client_adress_api"),
    path("update_client_api/<int:client_id>/", client_api.update_client_api, name="update_client_api"),
    path("delete_client_api/<int:client_id>/", client_api.delete_client_api, name="delete_client_api"),
    path("search_clients_api/", client_api.search_clients_api, name="search_clients_api"),
    path("create_feedback_link_api/", client_feedback_api.create_feedback_link_api, name="create_feedback_link_api"),
    path("create_client_feedback_api/", client_feedback_api.create_client_feedback_api, name="create_client_feedback_api"),
    path("create_client_feedback_api/", client_feedback_api.create_client_feedback_api, name="create_client_feedback_api"),
    # Work Order APIs
    path("create_work_order_api/", work_order_api.create_work_order_api, name="create_work_order_api"),
    path("create_work_order_download_link_api/",work_order_api.create_work_order_download_link_api, name="create_work_order_download_link_api"),
    path("list_work_orders_api/",work_order_api.list_work_orders_api, name="list_work_orders_api"),
    path("get_work_order_api/<int:work_order_id>/",work_order_api.get_work_order_api, name="get_work_order_api"),
    path("update_work_order_api/<int:work_order_id>/",work_order_api.update_work_order_api, name="update_work_order_api"),
    path("assign_work_order_api/<int:work_order_id>/",work_order_api.assign_work_order_api, name="assign_work_order_api"),
    path("get_work_order_status_history_api/<int:work_order_id>/",work_order_api.get_work_order_status_history_api, name="get_work_order_status_history_api")
]
