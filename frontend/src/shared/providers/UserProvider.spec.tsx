import { useContext } from "react";

import { render, screen } from "@testing-library/react";

import type { Me } from "~api/ffc-api-model";

import { UserContext } from "./UserContext";
import { UserProvider } from "./UserProvider";

const mockUseMeApi = jest.fn();

jest.mock("~shared/api/useMeApi", () => ({
  useMeApi: () => mockUseMeApi(),
}));

function UserConsumer() {
  const user = useContext(UserContext);

  return <div data-testid="user-role">{user?.account?.type ?? "missing"}</div>;
}

describe("UserProvider", () => {
  it("does not render children until the current user is available", () => {
    mockUseMeApi.mockReturnValue({ data: undefined });

    render(
      <UserProvider>
        <UserConsumer />
      </UserProvider>,
    );

    expect(screen.queryByTestId("user-role")).not.toBeInTheDocument();
  });

  it("provides the loaded user to descendants", () => {
    mockUseMeApi.mockReturnValue({
      data: {
        account: { type: "admin" },
      } as Me,
    });

    render(
      <UserProvider>
        <UserConsumer />
      </UserProvider>,
    );

    expect(screen.getByTestId("user-role")).toHaveTextContent("admin");
  });
});
