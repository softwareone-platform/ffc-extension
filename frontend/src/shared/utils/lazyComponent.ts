/**
 * Lazy adapter: turn a `import('...')` of a feature module + a named export
 * into the `{ Component }` shape react-router's `lazy` expects.
 *
 * Lets us point routes directly at feature components without a `routes/`
 * indirection layer, while keeping per-route code-splitting.
 */
export const lazyComponent =
  <K extends string>(importer: () => Promise<Record<K, React.ComponentType>>, exportName: K) =>
  async () => ({ Component: (await importer())[exportName] });
