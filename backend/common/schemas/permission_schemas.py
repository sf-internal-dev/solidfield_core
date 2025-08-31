ACTIONS_BY_PERMISSION_SCHEMA = {
    "L1": {
        "label": "Execution (Field Level)",
        # Field-level technicians can perform their assigned tasks, upload evidence, and request new service orders.
        "actions": [
            {
                "code": "service_order_request",
                "label": "Request Service Order",
                "delegable": False,
                "description": "Request the creation of a new service order to the supervisor or manager."
            },
            {
                "code": "view_assigned_service_orders",
                "label": "View Assigned Service Orders",
                "delegable": False,
                "description": "Can view and operate only on their assigned service orders."
            },
            {
                "code": "update_service_order_status",
                "label": "Update Service Order Status",
                "delegable": True,
                "description": "Can move the service order through allowed status transitions."
            },
            {
                "code": "submit_checklist",
                "label": "Submit Checklist",
                "delegable": True,
                "description": "Fills out and submits the service order checklist."
            },
            {
                "code": "upload_photos",
                "label": "Upload Photos",
                "delegable": True,
                "description": "Can attach photos to the assigned service order."
            },
            {
                "code": "collect_signature",
                "label": "Collect Client Signature",
                "delegable": True,
                "description": "Can capture the client’s digital signature."
            },
            {
                "code": "generate_feedback_link",
                "label": "Generate Feedback Link",
                "delegable": True,
                "description": "Generates a feedback link after completing the service order."
            }
        ]
    },
    "L2": {
        "label": "Coordination (Local Supervision)",
        "inherits_selectively_from": {
            "L1": ["service_order_request","view_assigned_service_orders", "collect_signature","update_service_order_status",
                   "generate_feedback_link","upload_photos","submit_checklist"]
                },
        # Supervisors inherit L1 capabilities and can approve requests, create internal tasks, and organize their local team.
        "actions": [
            {
                "code": "approve_service_order_request",
                "label": "Approve Service Order Request (L1)",
                "delegable": True,
                "description": "Can approve or deny service order requests made by L1 technicians."
            },
            {
                "code": "create_internal_service_order",
                "label": "Create Internal Service Order",
                "delegable": True,
                "description": "Can create service orders for routine internal tasks."
            },
            {
                "code": "view_team_orders",
                "label": "View Team Service Orders",
                "delegable": True,
                "description": "Can view service orders assigned to their team members."
            },
            {
                "code": "group_assignment_visual",
                "label": "Visual Group Assignment",
                "delegable": True,
                "description": "Organizes team technician distribution without persisting in the database."
            }
        ]
    },
    "L3": {
        "label": "Full Control (Operational Management)",
        "inherits_selectively_from": {
            "L1": ["view_assigned_service_orders", "collect_signature","update_service_order_status",
                   "generate_feedback_link","upload_photos","submit_checklist"],
            "L2": ["group_assignment_visual","view_team_orders","create_internal_service_order",
                   "approve_service_order_request","view_team_orders"]
                },
        # Managers inherit all permissions and handle distribution, validation, escalation, and technician management.
        "actions": [
            {
                "code": "assign_service_order",
                "label": "Assign Service Order",
                "delegable": True,
                "description": "Assigns service orders to technicians or supervisors."
            },
            {
                "code": "reassign_service_order",
                "label": "Reassign Service Order",
                "delegable": True,
                "description": "Can reassign service orders to a different technician."
            },
            {
                "code": "validate_service_order",
                "label": "Validate Service Order",
                "delegable": True,
                "description": "Validates the execution of a service order before releasing it."
            },
            {
                "code": "return_service_order",
                "label": "Return Service Order for Adjustments",
                "delegable": True,
                "description": "Returns the service order to the technician for corrections."
            },
            {
                "code": "create_checklist_template",
                "label": "Create Checklist Template",
                "delegable": True,
                "description": "Can create and version operational checklist templates."
            },
            {
                "code": "edit_checklist_template",
                "label": "Edit Checklist Template",
                "delegable": True,
                "description": "Can edit existing versions of checklist templates."
            },
            {
                "code": "view_all_kpis",
                "label": "View All KPIs",
                "delegable": True,
                "description": "Has access to performance and productivity indicators."
            },
            {
                "code": "manage_technicians",
                "label": "Manage technicians",
                "delegable": False,
                "description": "Creates, edits, blocks, promotes, or demotes technician accounts."
            },
            {
                "code": "delegate_temporary_permissions",
                "label": "Delegate Temporary Permissions",
                "delegable": False,
                "description": "Can temporarily delegate permissions to other technicians."
            },
            {
                "code": "delegate_permission_level",
                "label": "Delegate Permission Level",
                "delegable": False,
                "description": "Can delegate permission levels to other technicians."
            },
            {
                "code": "create_technicians_aggroupment",
                "label": "Create Technicians Aggroupment",
                "delegable": True,
                "description": "Can create technicians aggroupment."
            },
            {
                "code": "register_client",
                "label": "Create Technicians Aggroupment",
                "delegable": True,
                "description": "Can create technicians aggroupment."
            },
        ]
    }
}
