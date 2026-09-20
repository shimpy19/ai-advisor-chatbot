import type { MessageOut } from "../lib/types";

interface MessageBubbleProps {
  message: MessageOut;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[300px] whitespace-pre-wrap text-[13.5px] leading-relaxed ${
          isUser
            ? "rounded-[12px_4px_12px_12px] bg-accent px-3.5 py-2.5 text-white"
            : "rounded-[4px_12px_12px_12px] bg-surface-soft px-3.5 py-2.5 text-[#1B2740]"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
