import { useId } from "react";

type IconProps = {
  className?: string;
  width?: number;
  height?: number;
};

export function AdobeIcon({ className, width = 32, height = 29 }: IconProps) {
  return (
    <svg
      className={className}
      width={width}
      height={height}
      viewBox="0 0 32 29"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M11.8419 0H0V28.3055L11.8419 0Z" fill="#FA0C00" />
      <path d="M20.1736 0H32V28.3055L20.1736 0Z" fill="#FA0C00" />
      <path
        d="M16.0077 10.4326L23.5448 28.3057H18.5998L16.3471 22.6153H10.8312L16.0077 10.4326Z"
        fill="#FA0C00"
      />
    </svg>
  );
}

type SellerFlagIconProps = IconProps & {
  rounded?: boolean;
};

export function SellerFlagIcon({
  className,
  width = 32,
  height = 32,
  rounded = true,
}: SellerFlagIconProps) {
  const clipId = useId();

  return (
    <svg
      className={className}
      width={width}
      height={height}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {rounded && (
        <clipPath id={clipId}>
          <rect width="32" height="32" rx="16" ry="16" />
        </clipPath>
      )}
      <g clipPath={rounded ? `url(#${clipId})` : undefined}>
        <path
          d="M16 0H32V4L30 6L32 8V12L30 14L32 16V20L30 22L32 24V28L16 30L0 28V24L2 22L0 20V16L16 0Z"
          fill="#EEEEEE"
        />
        <path
          d="M14 4H32V8H14V4ZM14 12H32V16H16L14 12ZM0 20H32V24H0V20ZM0 28H32V32H0V28Z"
          fill="#D80027"
        />
        <path d="M0 0H16V16H0V0Z" fill="#0052B4" />
        <path
          d="M11.6875 15.1875L15.25 12.625H10.875L14.4375 15.1875L13.0625 11L11.6875 15.1875ZM6.625 15.1875L10.1875 12.625H5.8125L9.375 15.1875L8 11L6.625 15.1875ZM1.5625 15.1875L5.125 12.625H0.75L4.3125 15.1875L2.9375 11L1.5625 15.1875ZM11.6875 10.125L15.25 7.5625H10.875L14.4375 10.125L13.0625 5.9375L11.6875 10.125ZM6.625 10.125L10.1875 7.5625H5.8125L9.375 10.125L8 5.9375L6.625 10.125ZM1.5625 10.125L5.125 7.5625H0.75L4.3125 10.125L2.9375 5.9375L1.5625 10.125ZM11.6875 5L15.25 2.4375H10.875L14.4375 5L13.0625 0.8125L11.6875 5ZM6.625 5L10.1875 2.4375H5.8125L9.375 5L8 0.8125L6.625 5ZM1.5625 5L5.125 2.4375H0.75L4.3125 5L2.9375 0.8125L1.5625 5Z"
          fill="#EEEEEE"
        />
      </g>
    </svg>
  );
}
