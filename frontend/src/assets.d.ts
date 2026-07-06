// Ambient declarations for image asset imports. Must live in a global (non-module)
// declaration file so the wildcard modules apply to value imports across the app.
declare module "*.png" {
  const src: string;
  export default src;
}
declare module "*.jpg" {
  const src: string;
  export default src;
}
declare module "*.jpeg" {
  const src: string;
  export default src;
}
declare module "*.webp" {
  const src: string;
  export default src;
}
declare module "*.gif" {
  const src: string;
  export default src;
}
