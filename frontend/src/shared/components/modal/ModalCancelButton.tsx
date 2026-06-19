import { Button } from "@swo/design-system/button";

import { useFixedT } from "~shared/hooks/useFixedT";

type Props = {
  onClick: () => void;
  isDisabled?: boolean;
};

export const ModalCancelButton = ({ onClick, isDisabled }: Props) => {
  const t = useFixedT("shared:actions");
  return (
    <Button type="text" onClick={onClick} isDisabled={isDisabled}>
      {t("cancel")}
    </Button>
  );
};
