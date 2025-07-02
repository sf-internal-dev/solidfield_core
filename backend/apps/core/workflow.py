DEFAULT_WORKFLOW = {
    "states": ["open", "in_progress", "finished", "awaiting_validation", "approved"],
    "transitions": [
        {"from": "open", "to": "in_progress"},
        {"from": "in_progress", "to": "finished"},
        {"from": "finished", "to": "awaiting_validation"},
        {"from": "awaiting_validation", "to": "approved"},
    ],
    "permissions": {
        "L1": ["in_progress", "finished"],
        "L2": ["in_progress","finished"],
        "L3": ["approved"]
    }
}

ACTION_SCHEMA = {
    "status_transition": {
        "label": "Status Transition",
        "model": "orders.ServiceOrder",
    },
    "photo_upload": {
        "label": "Photo Upload",
        "model": "orders.ServiceOrderPhoto",
    },
}

