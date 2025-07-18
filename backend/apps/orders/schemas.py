# Used for business rules related to the service order download link.
# The link is just the link. The reason a purpose schema exists
# is to make connections with a whole util-service business rules system
# and it's generation on corex

SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA = {
    "client_review":{
        "purpose_rules": 
            {"...":"",
             }
    },
    "client_receipt":{
        "purpose_rules":
            {"...":"",
             }
    },
    "audit_and_compliance":{
        "purpose_rules":
            {"...":"",
             }
    },
    "client_temporary_download":{
        "purpose_rules":
            {"...":"",
             }
    }
}