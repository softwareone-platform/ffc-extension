type StorageMap = Map<string, string>;

function createStorage(): Storage {
  const store: StorageMap = new Map();

  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.has(key) ? (store.get(key) as string) : null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, String(value));
    },
  };
}

function defineStorageGetter(name: "localStorage" | "sessionStorage", getter: () => Storage): void {
  Object.defineProperty(window, name, {
    configurable: true,
    get: getter,
  });
}

describe("safe-storage", () => {
  const originalLocalStorage = Object.getOwnPropertyDescriptor(window, "localStorage");
  const originalSessionStorage = Object.getOwnPropertyDescriptor(window, "sessionStorage");

  afterEach(() => {
    jest.resetModules();

    if (originalLocalStorage) {
      Object.defineProperty(window, "localStorage", originalLocalStorage);
    }
    if (originalSessionStorage) {
      Object.defineProperty(window, "sessionStorage", originalSessionStorage);
    }
  });

  it("installs an in-memory fallback when localStorage is inaccessible", async () => {
    const sessionStorage = createStorage();
    defineStorageGetter("localStorage", () => {
      throw new Error("SecurityError");
    });
    defineStorageGetter("sessionStorage", () => sessionStorage);

    await import("./safe-storage");

    window.localStorage.setItem("key", "value");
    window.localStorage.setItem("second", "two");

    expect(window.localStorage.getItem("key")).toBe("value");
    expect(window.localStorage.length).toBe(2);
    expect(window.localStorage.key(0)).toBe("key");
    expect(window.localStorage.key(1)).toBe("second");
    window.localStorage.removeItem("key");
    expect(window.localStorage.length).toBe(1);
    window.localStorage.clear();
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage).toBe(sessionStorage);
  });

  it("leaves accessible storage objects untouched", async () => {
    const localStorage = createStorage();
    const sessionStorage = createStorage();

    defineStorageGetter("localStorage", () => localStorage);
    defineStorageGetter("sessionStorage", () => sessionStorage);

    await import("./safe-storage");

    expect(window.localStorage).toBe(localStorage);
    expect(window.sessionStorage).toBe(sessionStorage);
    expect(() => window.localStorage.setItem("key", "value")).not.toThrow();
    expect(window.localStorage.getItem("key")).toBe("value");
  });
});
