# Used for business rules related to the service order download link.
# The link is just the link. The reason a purpose schema exists
# is to make connections with a whole util-service business rules system
# and it's generation on corex

SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA = {
    "client_review":{
        "label": "Client Review",
        "description": "Client Review service order given to the client for feedback",
        "purpose_rules": 
            {
             "client_as_first":True,
             "available_to_client":True,
             "access_level_required":"ANY",
             "include_technician_notes": False,
             "include_signature": False,
             "include_checklist": True,
             }
    },
    "client_receipt":{
        "label": "Client Receipt",
        "description": "Client Receipt given to the customer after operation",
        "purpose_rules":
            {"client_as_first":False,
             "available_to_client":True,
             "access_level_required":">L2",
             "include_signature": True,
             "include_technician_notes": False,
             "include_checklist": True,
             }
    },
    "audit_and_compliance":{
        "label": "Audit and Compliance",
        "description": "Complete service order for Audit and compliance",
        "purpose_rules":
            {"client_as_first":False,
             "access_level_required":"L3",
             "include_photos": True,
             "include_signature": True,
             "include_checklist": True,
             "include_technician_notes": True,
             "offline_friendly": False,
             }
    },
    "field_team_copy":{
        "label": "Field Team Copy",
        "description": "Offline copy to field team operation",
        "purpose_rules":
            {
             "client_as_first":False,
             "access_level_required":">L2",
             "include_photos": False,
             "include_signature": False,
             "include_checklist": True,
             "include_technician_notes": False,
             "offline_friendly": True,
            }
    }
}