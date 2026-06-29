import enum

MPT_ORDER_STATUS_PROCESSING = "Processing"
MPT_ORDER_STATUS_QUERYING = "Querying"
MPT_ORDER_STATUS_COMPLETED = "Completed"

PURCHASE_TEMPLATE_NAME = "Purchase"
PURCHASE_EXISTING_TEMPLATE_NAME = "PurchaseExisting"
TERMINATE_TEMPLATE_NAME = "Terminate"

ORDER_TYPE_PURCHASE = "Purchase"
ORDER_TYPE_TERMINATE = "Termination"

# MPT product template types
PROCESSING_TEMPLATE_TYPE = "OrderProcessing"
QUERYING_TEMPLATE_TYPE = "OrderQuerying"
COMPLETED_TEMPLATE_TYPE = "OrderCompleted"


class ProcessResult(enum.StrEnum):
    COMPLETE = "Complete"
    RESCHEDULE = "Reschedule"
    CANCEL = "Cancel"
    SKIP = "Skip"


class ExceptionSeverity(enum.StrEnum):
    WARNING = "Warning"
    ERROR = "Error"
    INFO = "Info"
