class ValidationError:
    def __init__(self, id, message):
        self.id = id
        self.message = message

    def to_dict(self, **kwargs):
        return {
            "id": self.id,
            "message": self.message.format(**kwargs),
        }


ERR_ORGANIZATION_NAME = ValidationError("FFC0001", "Organization name is required")
ERR_CURRENCY = ValidationError("FFC0002", "Currency is required")
ERR_ADMIN_CONTACT = ValidationError("FFC0003", "Administrator contact is required")
ERR_ORDER_TYPE_NOT_SUPPORTED = ValidationError(
    "FFC0004", "Order type `{order_type}` is not supported by FinOps"
)
ERR_DUE_DATE_IS_REACHED = ValidationError("EXT1000", "Due date is reached {due_date}")
ERR_DUE_DATE_NOT_SET = ValidationError("EXT1001", "No due date fulfillment parameter found.")
