import { InlineNotification } from "@swo/design-system/notification";

function toKeyedLines(error: string) {
  const occurrences = new Map<string, number>();

  return error.split("\n").map((text) => {
    const count = occurrences.get(text) ?? 0;
    occurrences.set(text, count + 1);
    return { key: `${text}_${count}`, text };
  });
}

export function InlineErrorNotification({ error }: { readonly error: string | null }) {
  if (!error) {
    return <></>;
  }

  return (
    <div className="modal-error">
      <InlineNotification status="error">
        {toKeyedLines(error.toString()).map(({ key, text }, i) => (
          <p key={key}>{i === 0 ? <strong>{text}</strong> : text}</p>
        ))}
      </InlineNotification>
    </div>
  );
}
