// Browser third-party storage policy can block `localStorage`/`sessionStorage`
// inside a cross-origin iframe (Safari ITP, Chrome incognito with strict
// settings). SDK components may try to persist state and crash on a `SecurityError`.
//
// Probe each storage; if it throws, install an in-memory `Storage` polyfill so
// callers get a working API instead of an exception.
//
// Mirrors mpt-extension-example/frontend/src/fixes/safe-storage.ts.

function createMemoryStorage(): Storage {
  const store = new Map<string, string>();
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

function isStorageAccessible(storage: () => Storage | undefined): boolean {
  try {
    const instance = storage();
    if (!instance) return false;
    const probe = "__swo_probe__";
    instance.setItem(probe, "1");
    instance.removeItem(probe);
    return true;
  } catch {
    return false;
  }
}

function installFallback(name: "localStorage" | "sessionStorage"): void {
  if (isStorageAccessible(() => (window as unknown as Record<string, Storage>)[name])) return;

  try {
    Object.defineProperty(window, name, {
      configurable: true,
      value: createMemoryStorage(),
    });
  } catch {
    // ignore — nothing more we can do in a hostile sandbox
  }
}

installFallback("localStorage");
installFallback("sessionStorage");
