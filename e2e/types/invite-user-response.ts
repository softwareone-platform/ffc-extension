export type InviteUserResponse = {
  name: string;
  email: string; // email format
  events: {
    created: {
      at: string; // date-time format
      by: {
        id: string; // user ID format FUSR-xxxx-xxxx
        type: 'user' | 'system';
        name: string;
      };
    };
    updated: {
      at: string; // date-time format
      by: {
        id: string; // user ID format FUSR-xxxx-xxxx
        type: 'user' | 'system';
        name: string;
      };
    };
  };
  id: string; // user ID format FUSR-xxxx-xxxx
  account_user: {
    status: 'invited' | 'invitation-expired' | 'active' | 'deleted';
    events: {
      created: {
        at: string; // date-time format
        by: {
          id: string; // user ID format FUSR-xxxx-xxxx
          type: 'user' | 'system';
          name: string;
        };
      };
      updated: {
        at: string;
        by: {
          id: string; // user ID format FUSR-xxxx-xxxx
          type: 'user' | 'system';
          name: string;
        };
      };
      deleted?: {
        at: string;
        by: {
          id: string; // user ID format FUSR-xxxx-xxxx
          type: 'user' | 'system';
          name: string;
        };
      };
    };
    id: string; //FAUR-xxxx-xxxx-xxxx
    account: {
      id: string; // FACC-xxxx-xxxx
      name: string;
      type: 'affiliate' | 'operations';
    };
    user: {
      name: string;
      email: string; // email format
      id: string; // user ID format FUSR-xxxx-xxxx
    };
    invitation_token: string;
    invitation_token_expires_at: string; // date-time format
  };
  status: 'draft' | 'active' | 'disabled' | 'deleted';
};
