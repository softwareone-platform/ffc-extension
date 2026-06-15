// Ambient module declarations for non-code asset imports.
// Allows TypeScript to resolve side-effect imports like:
//   import './styles.scss';
declare module "*.scss";
declare module "*.sass";
declare module "*.css";

declare global {
  // `var` is required so the symbol is exposed on `globalThis`; `let`/`const`
  // inside `declare global` are block-scoped and don't extend `typeof globalThis`.
  var __MPT__:
    | {
        context?: unknown;
        onChange?: (cb: (data: unknown) => void) => void;
        emit?: (event: string, data: unknown) => void;
        listen?: (event: string, handler: (data?: unknown) => void) => () => void;
      }
    | undefined;
}

export {};
