export const mockUseNotifyParentChildModal = jest.fn();

export const mockNotifyParentChildModalModule = {
  useNotifyParentChildModal: (open: boolean) => mockUseNotifyParentChildModal(open),
};
