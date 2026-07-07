// Ambient (non-module) declarations for CSS Modules.
// `*.module.scss` is compiled with esbuild's `local-css` loader and exposes a
// default export mapping original class names to hashed, unique ones:
//   import styles from "./Foo.module.scss";
//   <div className={styles["foo"]} />
// This more specific pattern takes precedence over the `*.scss` declaration.
// This file must stay a global script (no top-level import/export) so the
// wildcards participate in relative-import resolution under `moduleResolution: bundler`.
declare module "*.module.scss" {
  const classes: { readonly [key: string]: string };
  export default classes;
}
declare module "*.module.css" {
  const classes: { readonly [key: string]: string };
  export default classes;
}
