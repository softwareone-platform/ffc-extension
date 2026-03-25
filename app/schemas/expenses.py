from decimal import Decimal

from app.enums import DatasourceType
from app.schemas.core import CommonEventsSchema, IdSchema
from app.schemas.organizations import OrganizationReference


class DatasourceExpenseRead(IdSchema, CommonEventsSchema):
    datasource_id: str
    linked_datasource_id: str
    datasource_name: str
    linked_datasource_type: DatasourceType
    organization: OrganizationReference
    year: int
    day: int
    month: int
    expenses: Decimal
    total_expenses: Decimal
