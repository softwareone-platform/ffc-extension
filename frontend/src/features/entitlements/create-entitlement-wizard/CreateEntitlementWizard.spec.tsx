import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosResponse } from "axios";

import type { EntitlementRead } from "~api/ffc-api-model";
import type { useUserRole } from "~shared/hooks/useUserRole";
import { renderWithQueryClient } from "~test-utils";
import { makeEntitlement } from "~test-utils/factories";

import {
  mockGetErrorMessage,
  mockSave,
  mockStepContext,
  mockUseSteps,
  mockUseUserRole,
  mockValidForm,
  mockWizard,
} from "./CreateEntitlementWizard.spec.mocks";

import { CreateEntitlementWizard } from "./CreateEntitlementWizard";

type Me = NonNullable<ReturnType<typeof useUserRole>["user"]>;

function makeMe(account: Omit<Me["account"], "external_id">): Me {
  return { account: { external_id: "ext-1", ...account } } as Me;
}

const REVIEW_STEP_INDEX = 2;
const SAVE_ERROR = "Saving failed";

function lastWizardProps() {
  return mockWizard.mock.lastCall![0];
}

function renderWizard(onClose = jest.fn()) {
  const user = userEvent.setup();
  renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={onClose} />);
  return { user, onClose };
}

async function fillAndSubmit(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "fill form" }));
  await user.click(screen.getByRole("button", { name: "submit wizard" }));
}

function primeSaveSuccess() {
  mockSave.mockResolvedValue({
    data: makeEntitlement({ id: "ent-new" }),
  } as unknown as AxiosResponse<EntitlementRead>);
}

function primeSaveFailure() {
  mockSave.mockRejectedValue(new AxiosError("boom"));
  mockGetErrorMessage.mockReturnValue(SAVE_ERROR);
}

describe("CreateEntitlementWizard", () => {
  beforeEach(() => {
    mockUseUserRole.mockReturnValue({ user: null, role: "operations" });
    mockUseSteps.mockReturnValue([{ title: "1" }, { title: "2" }, { title: "3" }, { title: "4" }]);
    mockStepContext.activeStepIndex = 0;
  });

  it("passes the initial saving state to useSteps", () => {
    renderWizard();

    expect(mockUseSteps).toHaveBeenLastCalledWith(false);
  });

  it("passes the configured steps to the Wizard", () => {
    renderWizard();

    expect(lastWizardProps().stepsProps).toHaveLength(4);
  });

  it("opens on the first step", () => {
    renderWizard();

    expect(lastWizardProps().activeStepIndex).toBe(0);
  });

  it.each([
    ["affiliate", 0, "step-affiliate"],
    ["data source", 1, "step-datasource"],
    ["review", 2, "step-review"],
    ["summary", 3, "step-summary"],
  ] as const)("renders the %s step when it is active", (_name, index, testId) => {
    mockStepContext.activeStepIndex = index;

    renderWizard();

    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it("starts with no affiliate preselected for non-affiliate users", () => {
    renderWizard();

    expect(screen.getByTestId("step-affiliate")).toHaveAttribute("data-affiliate", "null");
  });

  it.each([
    ["the account integration", "aws", "aws"],
    ["the unknown integration when the account has none", null, "unknown"],
  ] as const)(
    "preselects the affiliate account with %s for affiliate users",
    (_scenario, integration, expectedIntegration) => {
      mockUseUserRole.mockReturnValue({
        user: makeMe({ id: "aff-1", name: "Affiliate 1", type: "affiliate", integration }),
        role: "affiliate",
      });

      renderWizard();

      expect(
        JSON.parse(screen.getByTestId("step-affiliate").getAttribute("data-affiliate")!),
      ).toEqual({ id: "aff-1", name: "Affiliate 1", integration: expectedIntegration });
    },
  );

  it("closing the wizard reports an unsuccessful result when nothing was created", async () => {
    const { user, onClose } = renderWizard();

    await user.click(screen.getByRole("button", { name: "close wizard" }));

    expect(onClose).toHaveBeenCalledWith({ success: false });
  });

  it("saving the wizard reports an unsuccessful result when nothing was created", async () => {
    const { user, onClose } = renderWizard();

    await user.click(screen.getByRole("button", { name: "save wizard" }));

    expect(onClose).toHaveBeenCalledWith({ success: false });
  });

  it("dismissing the modal closes without a result", async () => {
    const { user, onClose } = renderWizard();

    await user.click(screen.getByRole("button", { name: "dismiss modal" }));

    expect(onClose).toHaveBeenCalledWith();
  });

  describe("submitting", () => {
    it("does not save when the form is invalid", async () => {
      const { user } = renderWizard();

      await user.click(screen.getByRole("button", { name: "submit wizard" }));

      expect(mockSave).not.toHaveBeenCalled();
    });

    it("saves the entitlement on behalf of the selected affiliate for operations users", async () => {
      primeSaveSuccess();
      const { user } = renderWizard();

      await fillAndSubmit(user);

      await waitFor(() => {
        expect(mockSave).toHaveBeenCalledWith(
          {
            name: mockValidForm.name,
            affiliate_external_id: mockValidForm.dataSource.affiliate_external_id,
            datasource_id: mockValidForm.dataSource.id,
            owner: { id: mockValidForm.affiliate.id },
          },
          expect.anything(),
        );
      });
    });

    it("saves the entitlement without an owner for affiliate users", async () => {
      mockUseUserRole.mockReturnValue({
        user: makeMe({ id: "acc-1", name: "Affiliate 1", type: "affiliate", integration: "aws" }),
        role: "affiliate",
      });
      primeSaveSuccess();
      const { user } = renderWizard();

      await fillAndSubmit(user);

      await waitFor(() => {
        expect(mockSave).toHaveBeenCalledWith(
          {
            name: mockValidForm.name,
            affiliate_external_id: mockValidForm.dataSource.affiliate_external_id,
            datasource_id: mockValidForm.dataSource.id,
          },
          expect.anything(),
        );
      });
    });

    it("advances to the next step after a successful save", async () => {
      primeSaveSuccess();
      const { user } = renderWizard();

      await fillAndSubmit(user);

      await waitFor(() => {
        expect(lastWizardProps().activeStepIndex).toBe(1);
      });
    });

    it.each([
      ["closing", "close wizard"],
      ["finishing", "save wizard"],
    ])("%s the wizard reports a successful result after a save", async (_name, button) => {
      primeSaveSuccess();
      const { user, onClose } = renderWizard();
      await fillAndSubmit(user);
      await waitFor(() => {
        expect(lastWizardProps().activeStepIndex).toBe(1);
      });

      await user.click(screen.getByRole("button", { name: button }));

      expect(onClose).toHaveBeenCalledWith({ success: true });
    });
  });

  describe("save errors", () => {
    beforeEach(() => {
      mockStepContext.activeStepIndex = REVIEW_STEP_INDEX;
      primeSaveFailure();
    });

    async function renderWithSaveError() {
      const { user, onClose } = renderWizard();
      await fillAndSubmit(user);
      await waitFor(() => {
        expect(screen.getByTestId("step-review")).toHaveAttribute("data-error", SAVE_ERROR);
      });
      return { user, onClose };
    }

    it("shows the error message and stays on the current step", async () => {
      await renderWithSaveError();

      expect(lastWizardProps().activeStepIndex).toBe(0);
    });

    it("reports an unsuccessful result when closed after a failed save", async () => {
      const { user, onClose } = await renderWithSaveError();

      await user.click(screen.getByRole("button", { name: "close wizard" }));

      expect(onClose).toHaveBeenCalledWith({ success: false });
    });

    it("clears the error once the user edits the form", async () => {
      const { user } = await renderWithSaveError();

      await user.click(screen.getByRole("button", { name: "change name" }));

      expect(screen.getByTestId("step-review")).toHaveAttribute("data-error", "");
    });

    it("keeps the error when form values change without making it dirty", async () => {
      const { user } = await renderWithSaveError();

      await user.click(screen.getByRole("button", { name: "change name without dirtying" }));

      expect(screen.getByTestId("step-review")).toHaveAttribute("data-error", SAVE_ERROR);
    });

    it("clears the error when the wizard is closed", async () => {
      const { user } = await renderWithSaveError();

      await user.click(screen.getByRole("button", { name: "close wizard" }));

      expect(screen.getByTestId("step-review")).toHaveAttribute("data-error", "");
    });
  });
});
