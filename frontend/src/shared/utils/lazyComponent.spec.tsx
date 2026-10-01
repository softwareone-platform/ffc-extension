import type { ReactNode } from "react";

import { lazyComponent } from "./lazyComponent";

function Alpha(): ReactNode {
  return "alpha";
}

function Beta(): ReactNode {
  return "beta";
}

describe("lazyComponent", () => {
  it("returns the requested named export as Component", async () => {
    const importer = jest.fn().mockResolvedValue({ Alpha, Beta });
    const load = lazyComponent(importer, "Alpha");

    await expect(load()).resolves.toEqual({ Component: Alpha });
    expect(importer).toHaveBeenCalledTimes(1);
  });

  it("can resolve a different named export from the same importer", async () => {
    const importer = jest.fn().mockResolvedValue({ Alpha, Beta });
    const load = lazyComponent(importer, "Beta");

    await expect(load()).resolves.toEqual({ Component: Beta });
  });
});
