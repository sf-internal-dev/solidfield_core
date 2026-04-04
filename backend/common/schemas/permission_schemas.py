ACTIONS_BY_PERMISSION_SCHEMA = {
    "L1": {
        "label": "Execution (Field Level)",
        # Field-level technicians can perform their assigned tasks, upload evidence, and request new work orders.
        "actions": [
            {
                "code": "work_order_request",
                "label": "Request Work Order",
                "delegable": False,
                "description": "Request the creation of a new work order to the supervisor or manager."
            },
            {
                "code": "view_assigned_work_orders",
                "label": "View Assigned Work Orders",
                "delegable": False,
                "description": "Can view and operate only on their assigned work orders."
            },
            {
                "code": "update_work_order_status",
                "label": "Update Work Order Status",
                "delegable": True,
                "description": "Can move the work order through allowed status transitions."
            },
            {
                "code": "submit_checklist",
                "label": "Submit Checklist",
                "delegable": True,
                "description": "Fills out and submits the work order checklist."
            },
            {
                "code": "upload_photos",
                "label": "Upload Photos",
                "delegable": True,
                "description": "Can attach photos to the assigned work order."
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
                "description": "Generates a feedback link after completing the work order."
            },
            {
                "code": "enqueue_offline_sync",
                "label": "Enqueue Offline Sync",
                "delegable": True,
                "description": "Queues payloads captured offline for later synchronization."
            },
            {
                "code": "process_offline_sync",
                "label": "Process Offline Sync Queue",
                "delegable": True,
                "description": "Applies pending offline queue items when connectivity is available."
            },
        ]
    },
    "L2": {
        "label": "Coordination (Local Supervision)",
        "inherits_selectively_from": {
            "L1": ["work_order_request","view_assigned_work_orders", "collect_signature","update_work_order_status",
                   "generate_feedback_link","upload_photos","submit_checklist",
                   "enqueue_offline_sync","process_offline_sync"]
                },
        # Supervisors inherit L1 capabilities and can approve requests, create internal tasks, and organize their local team.
        "actions": [
            {
                "code": "approve_work_order_request",
                "label": "Approve Work Order Request (L1)",
                "delegable": True,
                "description": "Can approve or deny work order requests made by L1 technicians."
            },
            {
                "code": "create_internal_work_order",
                "label": "Create Internal Work Order",
                "delegable": True,
                "description": "Can create work orders for routine internal tasks."
            },
            {
                "code": "view_team_orders",
                "label": "View Team Work Orders",
                "delegable": True,
                "description": "Can view work orders assigned to their team members."
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
            "L1": ["view_assigned_work_orders", "collect_signature","update_work_order_status",
                   "generate_feedback_link","upload_photos","submit_checklist",
                   "enqueue_offline_sync","process_offline_sync"],
            "L2": ["group_assignment_visual","view_team_orders","create_internal_work_order",
                   "approve_work_order_request","view_team_orders"]
                },
        # Managers inherit all permissions and handle distribution, validation, escalation, and technician management.
        "actions": [
            {
                "code": "assign_work_order",
                "label": "Assign Work Order",
                "delegable": True,
                "description": "Assigns work orders to technicians or supervisors."
            },
            {
                "code": "reassign_work_order",
                "label": "Reassign Work Order",
                "delegable": True,
                "description": "Can reassign work orders to a different technician."
            },
            {
                "code": "validate_work_order",
                "label": "Validate Work Order",
                "delegable": True,
                "description": "Validates the execution of a work order before releasing it."
            },
            {
                "code": "return_work_order",
                "label": "Return Work Order for Adjustments",
                "delegable": True,
                "description": "Returns the work order to the technician for corrections."
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
