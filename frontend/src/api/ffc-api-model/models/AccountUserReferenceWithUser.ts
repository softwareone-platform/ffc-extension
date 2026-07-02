/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AccountUserReferenceWithUser = {
  status: 'invited' | 'invitation-expired' | 'active' | 'deleted';
  id: string;
  created_at?: (string | null);
  joined_at?: (string | null);
  user: {
    name: string;
    external_id: string;
    email: string;
    id: string;
  };
};
