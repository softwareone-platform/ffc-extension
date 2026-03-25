from typing import Annotated

from fastapi import Path

from app.db import models

EntitlementId = Annotated[str, Path(pattern=models.Entitlement.build_id_regex())]
OrganizationId = Annotated[str, Path(pattern=models.Organization.build_id_regex())]
SystemId = Annotated[str, Path(pattern=models.System.build_id_regex())]
AccountId = Annotated[str, Path(pattern=models.Account.build_id_regex())]
UserId = Annotated[str, Path(pattern=models.User.build_id_regex())]
