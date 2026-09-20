import { useState } from "react";

interface MessageComposerProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function MessageComposer({
  onSend,
  disabled,
  placeholder = "Ask the advisor…",
  className = "",
}: MessageComposerProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  return (
    <form onSubmit={handleSubmit} className={`flex items-center gap-2.5 ${className}`}>
      <label htmlFor="composer-input" className="sr-only">
        Message the advisor
      </label>
      <input
        id="composer-input"
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="flex-1 rounded-[10px] border border-line bg-surface-soft px-3.5 py-2.5 text-[13.5px] text-ink outline-none disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[10px] bg-accent text-white disabled:opacity-50"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </form>
  );
}
