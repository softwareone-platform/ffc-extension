import TestUsers from '../test-data/test-users';

/** Whoever the spec projects run as owns the cached root URL. */
const rootUrlOwner = TestUsers.Admin;

/**
 * Builds an in-extension route from the URL the shell redirected to, keeping its query —
 * the account param it appends exists nowhere else, and the plug id is a templated
 * `meta.yaml` value rather than something the tests can reconstruct.
 *
 * Splits on `/-/` (the shell's context placeholder) instead of appending, so a cached URL
 * that already carries a default route still resolves siblings correctly.
 */
export function extensionRoute(route: string): string {
  const root = rootUrlOwner.extensionRootUrl;
  if (root === undefined) {
    throw new Error(
      `No extension root URL in ${rootUrlOwner.sessionStoragePath}. ` +
        'setup/auth.setup.ts stores it — run the suite through playwright.config.ts rather than a bare spec.'
    );
  }

  const url = new URL(root);
  const [plugPath] = url.pathname.split('/-/');
  url.pathname = `${plugPath}/-/${route}`;
  return url.toString();
}
