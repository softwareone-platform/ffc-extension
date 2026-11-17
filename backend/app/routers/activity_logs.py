from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select

from app.db.handlers import NotFoundError
from app.db.models import ActivityLog
from app.dependencies.db import ActivityLogRepository
from app.dependencies.path import ActivityLogId
from app.pagination import LimitOffsetPage, paginate
from app.rql import ActivityLogRules, RQLQuery
from app.schemas.activity_logs import ActivityLogDetailRead, ActivityLogRead
from app.schemas.core import convert_model_to_schema

router = APIRouter()


async def fetch_activity_log_or_404(
    activity_log_id: ActivityLogId,
    activity_logs_repo: ActivityLogRepository,
) -> ActivityLog:
    try:
        return await activity_logs_repo.get_with_changes(id=activity_log_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "",
    response_model=LimitOffsetPage[ActivityLogRead],
)
async def get_activity_logs(
    activity_logs_repo: ActivityLogRepository,
    base_query: Select = Depends(RQLQuery(ActivityLogRules())),
):
    return await paginate(
        handler=activity_logs_repo,
        schema_cls=ActivityLogRead,
        base_query=base_query,
    )


@router.get(
    "/{activity_log_id}",
    response_model=ActivityLogDetailRead,
)
async def get_activity_log_by_id(
    activity_log: Annotated[ActivityLog, Depends(fetch_activity_log_or_404)],
):
    return convert_model_to_schema(ActivityLogDetailRead, activity_log)
