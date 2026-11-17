import { useParams } from "react-router-dom";

export enum ContentType {
  DataSource = "dataSource",
  Organization = "organization",
  Unknown = "unknown",
}

export function useContentType(): ContentType {
  const { dataSourceId, organizationId } = useParams();

  if (dataSourceId) {
    return ContentType.DataSource;
  }
  if (organizationId) {
    return ContentType.Organization;
  }

  return ContentType.Unknown;
}
