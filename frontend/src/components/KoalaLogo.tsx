interface KoalaLogoProps {
  size?: number;
}

export function KoalaLogo({ size = 30 }: KoalaLogoProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="shrink-0">
      <rect x="0" y="0" width="32" height="32" rx="9" className="fill-accent" />
      <circle cx="8.2" cy="9.4" r="5.3" fill="#fff" />
      <circle cx="23.8" cy="9.4" r="5.3" fill="#fff" />
      <circle cx="8.2" cy="9.4" r="2.5" className="fill-accent" />
      <circle cx="23.8" cy="9.4" r="2.5" className="fill-accent" />
      <circle cx="16" cy="18.3" r="9" fill="#fff" />
      <path
        d="M10.6 17.1 Q12.4 18.7 14.2 17.1"
        stroke="#0F1729"
        strokeWidth="1.6"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M17.8 17.1 Q19.6 18.7 21.4 17.1"
        stroke="#0F1729"
        strokeWidth="1.6"
        fill="none"
        strokeLinecap="round"
      />
      <ellipse cx="16" cy="20.7" rx="2.9" ry="2.3" fill="#0F1729" />
    </svg>
  );
}
