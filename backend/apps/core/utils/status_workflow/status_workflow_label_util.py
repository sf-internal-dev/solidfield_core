from backend.common.work_order_status_workflow import DEFAULT_STATUS_WORKFLOW

# -> Returns the status workflow JSON for a given tenant
# Falls back to DEFAULT_STATUS_WORKFLOW if the tenant has no custom workflow
def get_workflow_for_tenant(tenant):
    try:
        return tenant.status_workflow.workflow_json
    except tenant.status_workflow.workflow_json.DoesNotExist:
        return DEFAULT_STATUS_WORKFLOW


# -> Converts a snake_case status string into a human-readable label
# Example: "in_progress" → "In Progress"
def get_workflow_status_label(status: str) -> str:
    return ' '.join(part.capitalize() for part in status.split('_'))

# -> Generates a dictionary mapping each state in the workflow to a readable label
# Example output: {"in_progress": "In Progress", "completed": "Completed"}
def generate_labels_for_workflow(workflow: dict) -> dict:
    return {state: get_workflow_status_label(state) for state in workflow.get("states", [])}