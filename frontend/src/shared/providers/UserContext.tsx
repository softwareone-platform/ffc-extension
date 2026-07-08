import { createContext } from "react";

import { Me } from "~api/ffc-api-model";

export const UserContext = createContext<Me | undefined>(undefined);
