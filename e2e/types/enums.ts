export enum ERequestMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH',
}

export enum EDatasourceType {
  AWS_CNR = 'aws_cnr',
  AZURE_CNR = 'azure_cnr',
  AZURE_TENANT = 'azure_tenant',
  GCP_CNR = 'gcp_cnr',
  UNKNOWN = 'unknown',
}

export enum EUserStatus {
  INVITED = 'invited',
  INVITATION_EXPIRED = 'invitation-expired',
  ACTIVE = 'active',
  DELETED = 'deleted',
}

export enum EStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  DISABLED = 'disabled',
  DELETED = 'deleted',
}
