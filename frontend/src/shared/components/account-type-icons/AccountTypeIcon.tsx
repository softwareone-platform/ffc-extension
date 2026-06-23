import { ReactElement, useEffect, useState } from "react";

type IconProps = {
  name: string;
  width?: number;
  height?: number;
  size?: number;
  boxWidth?: number;
  boxHeight?: number;
  className?: string;
};

function AccountTypeIcon({
  name,
  width,
  height,
  size,
  boxWidth = 24,
  boxHeight = 24,
  className = "",
}: IconProps) {
  if (size !== undefined) {
    width = size;
    height = size;
  } else {
    width = width ?? 24;
    height = height ?? 24;
  }

  const [viewBox, setViewBox] = useState<string>(`0 0 ${boxWidth} ${boxHeight}`);

  useEffect(() => setViewBox(`0 0 ${boxWidth} ${boxHeight}`), [boxHeight, boxWidth]);

  const [iconContent, setIconContent] = useState<ReactElement>();
  useEffect(() => {
    if (!name) {
      return;
    }

    import(`./icons/${name}.tsx`)
      .then((module) => {
        setIconContent(module.default);
      })
      .catch((error) => {
        console.error(`Error loading icon: ${name}`, error);
      });
  }, [name]);

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={viewBox}
      width={width}
      height={height}
      className={className}
    >
      {iconContent}
    </svg>
  );
}

export default AccountTypeIcon;
