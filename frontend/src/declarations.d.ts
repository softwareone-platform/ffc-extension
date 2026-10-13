// CSS modules: `styles.foo` resolves to the generated scoped class name.
// Must be declared before the catch-all below so it wins for `*.module.scss`.
declare module "*.module.scss" {
  const classes: { readonly [key: string]: string };
  export default classes;
}

// Plain stylesheets are imported for their side effect (injected <style> tag).
declare module "*.scss";
