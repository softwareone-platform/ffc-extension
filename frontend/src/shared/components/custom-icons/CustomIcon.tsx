import { ReactElement, useEffect, useState } from "react";

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
        // if (viewBox) {
        //   setViewBox(viewBox);
        // }
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

export default CustomIcon;
