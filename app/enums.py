import enum


@enum.unique
class ActorType(str, enum.Enum):
    USER = "user"
    SYSTEM = "system"


@enum.unique
class EntitlementStatus(str, enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    TERMINATED = "terminated"
    DELETED = "deleted"


@enum.unique
class SystemStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@enum.unique
class UserStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@enum.unique
class AccountUserStatus(str, enum.Enum):
    INVITED = "invited"
    INVITATION_EXPIRED = "invitation-expired"
    ACTIVE = "active"
    DELETED = "deleted"


@enum.unique
class AccountType(str, enum.Enum):
    OPERATIONS = "operations"
    AFFILIATE = "affiliate"


@enum.unique
class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@enum.unique
class DatasourceType(str, enum.Enum):
    AWS_CNR = "aws_cnr"
    AZURE_CNR = "azure_cnr"
    AZURE_TENANT = "azure_tenant"
    GCP_CNR = "gcp_cnr"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


@enum.unique
class OrganizationStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DELETED = "deleted"
