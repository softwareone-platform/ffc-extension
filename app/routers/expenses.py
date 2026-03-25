from fastapi import APIRouter, Depends
from sqlalchemy import Select

from app.dependencies.db import DatasourceExpenseRepository
from app.pagination import LimitOffsetPage, paginate
from app.rql import DatasourceExpenseRules, RQLQuery
from app.schemas.expenses import DatasourceExpenseRead

router = APIRouter()


@router.get("", response_model=LimitOffsetPage[DatasourceExpenseRead])
async def list_datasource_expenses(
    datasource_expense_repo: DatasourceExpenseRepository,
    base_query: Select = Depends(RQLQuery(DatasourceExpenseRules())),
):
    return await paginate(datasource_expense_repo, DatasourceExpenseRead, base_query=base_query)
