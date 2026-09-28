describe("useFixedT", () => {
  it("returns the translator from useTranslation with the provided key prefix", async () => {
    jest.resetModules();
    jest.unmock("~shared/hooks/useFixedT");
    const t = jest.fn();
    jest.doMock("react-i18next", () => ({
      useTranslation: () => ({ t }),
    }));

    const { useFixedT } = await import("~shared/hooks/useFixedT");

    expect(useFixedT("shared:grid")).toBe(t);
  });
});

