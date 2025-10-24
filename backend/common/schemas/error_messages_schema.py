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
        "message": "As a {label}, you has no permission permission to perform this action.",
        "type": "negative"
    },
    "delegator_not_manager": {
        "message": "Delegation failed: the delegator is not a manager/L3.",
        "type": "negative"
    },
    "tried_to_delegate_to_itself": {
        "message": "Delegation failed: a technician cannot delegate to themselves.",
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
    "technician_not_found": {
        "message": "The requested technician could not be found.",
        "type": "negative"
    },
    "cannot_delete_self": {
        "message": "You cannot delete your own account.",
        "type": "negative"
    },
    "invalid_username": {
        "message": "The provided username is invalid.",
        "type": "negative"
    },
    "invalid_social_name": {
        "message": "The provided social name is invalid.",
        "type": "negative"
    },
    "invalid_technician_permission": {
        "message": "The provided technician permission level is invalid.",
        "type": "negative"
    },
    "invalid_is_active": {
        "message": "The provided active status is invalid.",
        "type": "negative"
    },
    "tenant_not_found": {
        "message": "The requested tenant could not be found.",
        "type": "negative"
    },
    "slug_already_exists": {
        "message": "The provided slug is already in use by another tenant.",
        "type": "negative"
    },
    "invalid_tenant_name": {
        "message": "The provided tenant name is invalid.",
        "type": "negative"
    },
    "invalid_slug_format": {
        "message": "The provided slug format is invalid.",
        "type": "negative"
    },
    "invalid_hex_color": {
        "message": "The provided color is not a valid hex color.",
        "type": "negative"
    },
}


def get_error_payload(code: str) -> dict:
    """
    Given an error code, returns the error payload (message + type).
    If the code has dynamic arguments (ex.: 'invalid_action:delete'),
    they will be interpolated into the message.
    """
    # Verifica se tem argumentos no código
    if ":" in code:
        base_key, arg_part = code.split(":", 1)

        # Procurar uma chave no dicionário que comece com base_key + ":"
        for template_key, payload in ERROR_MESSAGES.items():
            if template_key.startswith(base_key + ":"):
                message_template = payload["message"]

                # Extrair placeholders do template da chave
                # Ex.: "invalid_action:{action}" -> ["action"]
                import re
                placeholders = re.findall(r"{(\w+)}", template_key)

                # Se houver múltiplos placeholders, tentar separar por delimitadores
                values = arg_part.split("->") if "->" in template_key else arg_part.split(":")

                # Montar dicionário {placeholder: valor}
                mapping = dict(zip(placeholders, values))

                return {
                    "message": message_template.format(**mapping),
                    "type": payload["type"]
                }

    # Caso seja um erro fixo
    if code in ERROR_MESSAGES:
        return ERROR_MESSAGES[code]

    # Retorno padrão se não achar
    return {
        "message": f"Unknown error code: {code}",
        "type": "negative"
    }

if __name__ == "__main__":
    print(get_error_payload("transition_not_allowed:bla->blabla"))
    print(get_error_payload("permission_denied_for_state:blablabla"))
    print(get_error_payload("item_not_found_by_order:#SOLIWO0001"))
    print(get_error_payload("technician_has_no_permission:L2"))

# {'message': 'Transition from bla to blabla is not allowed.', 'type': 'negative'}
# {'message': 'You do not have permission to change the status to blablabla.', 'type': 'negative'}
# {'message': 'Item with order #SOLIWO0001 was not found.', 'type': 'negative'}
# {'message': 'As a L2, you has no permission permission to perform this action.', 'type': 'negative'}