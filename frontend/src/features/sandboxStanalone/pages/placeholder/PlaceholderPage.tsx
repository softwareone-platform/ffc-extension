import { BoldText, RegularText } from "@swo/design-system/text";

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div>
      <BoldText size={4}>{title}</BoldText>
      <RegularText color="grey-5">This section is not available yet.</RegularText>
    </div>
  );
}
