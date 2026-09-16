import { InlineNotification } from "@swo/design-system/notification";

export function InlineErrorNotification({ error }: { readonly error: string | null }) {
  if (!error) {
    return <></>;
  }

  return (
    <div className="modal-error">
      <InlineNotification status="error">
        {error
          .toString()
          .split("\n")
          .map((err, i) => {
            return <p key={"error_" + i}>{i === 0 ? <strong>{err}</strong> : err}</p>;
          })}
      </InlineNotification>
    </div>
  );
}
