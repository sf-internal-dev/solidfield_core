ERROR_MESSAGES = {
    "required_value_missing": {
        "message": "A required value is missing. Please fill in all mandatory fields.",
        "type": "negative"
    },
    "choice_not_in_options": {
        "message": "The selected option is not valid. Please choose a valid option.",
        "type": "negative"
    },
    "item_answer_not_found": {
        "message": "The requested answer could not be found. Please try again.",
        "type": "negative"
    },
    "would_violate_min_groups": {
        "message": "This action would violate the minimum group requirements.",
        "type": "negative"
    },
    "item_not_found_by_order:{order}": {
        "message": "Item with order {order} was not found.",
        "type": "negative"
    },
    "invalid_person_type": {
        "message": "The provided person type is invalid.",
        "type": "negative"
    },
    "invalid_document_id": {
        "message": "The provided document ID is invalid.",
        "type": "negative"
    },
    "invalid_phone_number": {
        "message": "The provided phone number is invalid.",
        "type": "negative"
    },
    "invalid_email": {
        "message": "The provided email address is invalid.",
        "type": "negative"
    },
    "invalid_postal_code": {
        "message": "The provided postal code is invalid.",
        "type": "negative"
    },
    "invalid_region_code": {
        "message": "The provided region code is invalid.",
        "type": "negative"
    },
    "invalid_coordinates": {
        "message": "The provided coordinates are invalid.",
        "type": "negative"
    },
    "key_generation_failed": {
        "message": "A system error occurred while generating the key. Please try again.",
        "type": "negative"
    },
    "invalid_stars_value": {
        "message": "The rating value is invalid. Please provide a valid number of stars.",
        "type": "negative"
    },
    "comment_too_long": {
        "message": "Your comment is too long. Please shorten it and try again.",
        "type": "negative"
    },
    "tenant_not_found": {
        "message": "The requested tenant could not be found.",
        "type": "negative"
    },
    "malformed_workflow": {
        "message": "The workflow definition is invalid or corrupted.",
        "type": "negative"
    },
    "transition_not_allowed:{current_status}->{new_status}": {
        "message": "Transition from {current_status} to {new_status} is not allowed.",
        "type": "negative"
    },
    "permission_denied_for_state:{new_status}": {
        "message": "You do not have permission to change the status to {new_status}.",
        "type": "negative"
    },
    "technician_has_no_permission:{label}": {
        "message": "The technician does not have permission to perform action: {label}.",
        "type": "negative"
    },
    "delegator_not_manager": {
        "message": "Delegation failed: the delegator is not a manager.",
        "type": "negative"
    },
    "tried_to_delegate_to_itself": {
        "message": "Delegation failed: a user cannot delegate to themselves.",
        "type": "negative"
    },
    "invalid_action:{action}": {
        "message": "The action '{action}' is not valid.",
        "type": "negative"
    },
    "no_valid_actions": {
        "message": "There are no valid actions available at this time.",
        "type": "negative"
    },
}
