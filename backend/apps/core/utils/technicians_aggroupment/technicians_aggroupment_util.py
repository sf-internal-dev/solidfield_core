
# função que faça a adição automatica de tag ao agrupamento
# as tags serão A B C D
# apenas 4 agrupamentos por vez serão permitidos
# cada agrupamento precisa de ao menos 2 pessoas

def check_reached_aggroupment_limit(last_aggroupment_tag: str) -> bool:
    if last_aggroupment_tag != None:
        return True if last_aggroupment_tag == "D" else False
    return False

def define_aggroupment_tag(company_last_aggroupment):
    if check_reached_aggroupment_limit(company_last_aggroupment):
        pass
    if company_last_aggroupment == None:
        return "A"
    if company_last_aggroupment == "A":
        return "B"
    if company_last_aggroupment == "B":
        return "C"
    if company_last_aggroupment == "C":
        return "D"

def allowed_aggroupment(members_count: int) -> bool:
    return True if members_count >= 2 else False