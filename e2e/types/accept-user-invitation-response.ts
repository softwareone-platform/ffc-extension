export type AcceptUserInvitationResponse = {
  name: string;
  email: string; //email format
  events: {
    created: {
      at: string; //date-time format
      by: {
        id: string; // user format FUSR-xxxx-xxxx
        type: 'user' | 'system';
        name: string;
      };
    };
    updated: {
      at: string; //date-time format
      by: {
        id: string; // user format FUSR-xxxx-xxxx
        type: 'user' | 'system';
        name: string;
      };
    };
    deleted?: {
      at: string; //date-time format
      by: {
        id: string; // user format FUSR-xxxx-xxxx}
        type: 'user' | 'system';
        name: string;
      };
    };
  };
  id: string; // user format FUSR-xxxx-xxxx
  status: string; // 'draft' | 'active' | 'disabled' | 'deleted'
  last_used_account: {
    id: string; // account format FACC-xxxx-xxxx
    name: string;
    type: 'operations' | 'affiliate';
  };
};
