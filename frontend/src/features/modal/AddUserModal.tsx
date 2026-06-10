import { useFixedT } from "~shared/hooks/useFixedT";

import "./ModalWidget.scss";

import { AddUser } from "~features/organizations/components/AddUserModal";

export default () => {
  const tUsers = useFixedT("organization:users");

  return (
    <div className="modal">
      <div className="modal-header modal__container">
        <div className="modal-header-title">{tUsers("add_user")}</div>
      </div>
      <AddUser />
    </div>
  );
};
