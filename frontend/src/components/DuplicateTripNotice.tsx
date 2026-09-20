import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { formatRelativeTime } from "../lib/format";
import type { DuplicateTripOut } from "../lib/types";

interface DuplicateTripNoticeProps {
  conversationId: string;
  duplicate: DuplicateTripOut;
}

const AUTO_DISMISS_MS = 10_000;
const FADE_MS = 300;

function storageKey(conversationId: string, duplicateConversationId: string): string {
  return `koalla:duplicate-trip-seen:${conversationId}:${duplicateConversationId}`;
}

function hasBeenSeen(key: string): boolean {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    // Private browsing / blocked storage — just means it may show again next time,
    // not worth failing over.
    return false;
  }
}

export function DuplicateTripNotice({ conversationId, duplicate }: DuplicateTripNoticeProps) {
  const key = storageKey(conversationId, duplicate.conversation_id);
  // Read once, synchronously, so an already-seen notice never flashes on screen —
  // it just doesn't render at all instead of rendering then immediately fading.
  const [alreadySeen] = useState(() => hasBeenSeen(key));
  const [visible, setVisible] = useState(true);
  const [mounted, setMounted] = useState(!alreadySeen);

  // Marked as seen the moment it's shown (not only on dismiss/fade) — this is what
  // makes it a once-ever notice per conversation pair, rather than reappearing on
  // every reload.
  useEffect(() => {
    if (alreadySeen) return;
    try {
      localStorage.setItem(key, "1");
    } catch {
      // Ignore — see hasBeenSeen above.
    }
  }, [alreadySeen, key]);

  // Auto-fades after 10s, but a manual dismiss (setVisible(false) below) skips
  // straight to the same fade — one shared path for both.
  useEffect(() => {
    if (alreadySeen) return;
    const timer = setTimeout(() => setVisible(false), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [alreadySeen]);

  useEffect(() => {
    if (visible) return;
    const timer = setTimeout(() => setMounted(false), FADE_MS);
    return () => clearTimeout(timer);
  }, [visible]);

  if (!mounted) return null;

  const dateBit =
    duplicate.start_date || duplicate.end_date
      ? ` (${duplicate.start_date ?? "?"} – ${duplicate.end_date ?? "?"})`
      : "";

  return (
    <div
      className={`absolute bottom-full left-3 right-3 z-10 mb-2 rounded-[22px] border border-line bg-accent-light px-4 py-3 shadow-md transition-opacity duration-300 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      <div className="flex items-start gap-2">
        <span className="flex-1 text-[12.5px] leading-relaxed text-ink-soft">
          You're already planning a trip to <strong>{duplicate.destination}</strong>
          {dateBit} in <strong>"{duplicate.title}"</strong> (
          {formatRelativeTime(duplicate.updated_at)}).
        </span>
        <button
          type="button"
          aria-label="Dismiss"
          onClick={() => setVisible(false)}
          className="shrink-0 text-faint hover:text-ink-soft"
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
      <Link
        to={`/conversations/${duplicate.conversation_id}`}
        className="mt-2 inline-block rounded-full bg-accent px-3 py-1 text-[11.5px] font-semibold text-white transition-all duration-150 hover:bg-[#1d4ed8]"
      >
        Go there
      </Link>
    </div>
  );
}
