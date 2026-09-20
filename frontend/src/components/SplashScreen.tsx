import { useEffect, useState } from "react";

interface SplashScreenProps {
  onDone: () => void;
}

const WAKE_AT_MS = 1500;
const FADE_AT_MS = 2500;
const FADE_DURATION_MS = 500;

// Plays once per welcome-page mount: Koalla starts asleep, wakes up, then the
// whole splash fades to reveal the normal welcome content underneath (which is
// already mounted and ready — this is an overlay, not a blocking loading state).
export function SplashScreen({ onDone }: SplashScreenProps) {
  const [awake, setAwake] = useState(false);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const wakeTimer = setTimeout(() => setAwake(true), WAKE_AT_MS);
    const fadeTimer = setTimeout(() => setFading(true), FADE_AT_MS);
    const doneTimer = setTimeout(onDone, FADE_AT_MS + FADE_DURATION_MS);
    return () => {
      clearTimeout(wakeTimer);
      clearTimeout(fadeTimer);
      clearTimeout(doneTimer);
    };
  }, [onDone]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-accent transition-opacity duration-[500ms] ${
        fading ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="relative">
        <svg width="88" height="88" viewBox="0 0 32 32" aria-hidden="true">
          <circle cx="8.2" cy="9.4" r="5.3" fill="#fff" />
          <circle cx="23.8" cy="9.4" r="5.3" fill="#fff" />
          <circle cx="8.2" cy="9.4" r="2.5" fill="#2563eb" />
          <circle cx="23.8" cy="9.4" r="2.5" fill="#2563eb" />
          <circle cx="16" cy="18.3" r="9" fill="#fff" />

          {/* Sleepy, closed eyes — fade out on waking */}
          <g
            className={`transition-opacity duration-300 ${awake ? "opacity-0" : "opacity-100"}`}
          >
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
          </g>

          {/* Open eyes — fade in on waking */}
          <g
            className={`transition-opacity duration-300 ${awake ? "opacity-100" : "opacity-0"}`}
          >
            <circle cx="12.4" cy="17.3" r="1.5" fill="#0F1729" />
            <circle cx="19.6" cy="17.3" r="1.5" fill="#0F1729" />
          </g>

          <ellipse cx="16" cy="20.7" rx="2.9" ry="2.3" fill="#0F1729" />
        </svg>

        <div
          className={`font-display absolute -right-2 -top-4 animate-float text-xl font-bold text-white transition-opacity duration-300 ${
            awake ? "opacity-0" : "opacity-100"
          }`}
        >
          z
        </div>
      </div>

      <div className="font-display mt-4 text-[13px] font-semibold text-white/85">
        {awake ? "Ready when you are…" : "Waking up Koalla…"}
      </div>
    </div>
  );
}
