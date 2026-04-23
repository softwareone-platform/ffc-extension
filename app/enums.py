import enum


@enum.unique
class ActorType(enum.StrEnum):
    USER = "user"
    SYSTEM = "system"


@enum.unique
class EntitlementStatus(enum.StrEnum):
    NEW = "new"
    ACTIVE = "active"
    TERMINATED = "terminated"
    DELETED = "deleted"


@enum.unique
class SystemStatus(enum.StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@enum.unique
class UserStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@enum.unique
class AccountUserStatus(enum.StrEnum):
    INVITED = "invited"
    INVITATION_EXPIRED = "invitation-expired"
    ACTIVE = "active"
    DELETED = "deleted"


@enum.unique
class AccountType(enum.StrEnum):
    ADMIN = "admin"
    OPERATIONS = "operations"
    AFFILIATE = "affiliate"


@enum.unique
class AccountStatus(enum.StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@enum.unique
class DatasourceType(enum.StrEnum):
    AWS_CNR = "aws_cnr"
    AZURE_CNR = "azure_cnr"
    AZURE_TENANT = "azure_tenant"
    GCP_CNR = "gcp_cnr"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


@enum.unique
class OrganizationStatus(enum.StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DELETED = "deleted"
