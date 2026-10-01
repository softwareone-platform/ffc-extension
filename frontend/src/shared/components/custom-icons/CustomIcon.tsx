import { ReactElement, useEffect, useState } from "react";

import unknownIcon from "./icons/unknown";

type IconProps = {
  readonly name: string;
  readonly width?: number;
  readonly height?: number;
  readonly size?: number;
  readonly boxWidth?: number;
  readonly boxHeight?: number;
  readonly className?: string;
};

function CustomIcon({
  name,
  width,
  height,
  size,
  boxWidth = 24,
  boxHeight = 24,
  className = "",
}: IconProps) {
  if (size === undefined) {
    width = width ?? 24;
    height = height ?? 24;
  } else {
    width = size;
    height = size;
  }

  const [iconContent, setIconContent] = useState<ReactElement>();

  useEffect(() => {
    if (!name) {
      return;
    }

    const asyncImport = async (name: string) => {
      const module = await import(`./icons/${name}.tsx`);
      setIconContent(module.default);
    };

    const availableIcons: string[] = [
      "aws",
      "aws_cnr",
      "azure_cnr",
      "azure_tenant",
      "gcp_cnr",
      "gcp_tenant",
      "google",
      "microsoft",
      "unknown",
    ];

    asyncImport(availableIcons.includes(name) ? name : "unknown");
  }, [name]);

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${boxWidth} ${boxHeight}`}
      width={width}
      height={height}
      className={className}
    >
      {iconContent ?? unknownIcon}
    </svg>
  );
}

export default CustomIcon;
