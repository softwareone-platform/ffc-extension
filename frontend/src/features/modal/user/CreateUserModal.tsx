import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalWidget } from "../shared/ModalWidget";
import { UserForm } from "./UserForm";

export default () => {
  const tUsers = useFixedT("organization:users");

  return (
    <ModalWidget title={tUsers("add_user")}>
      <UserForm />
    </ModalWidget>
  );
};
