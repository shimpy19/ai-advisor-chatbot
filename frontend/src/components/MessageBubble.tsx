import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { MessageOut } from "../lib/types";

interface MessageBubbleProps {
  message: MessageOut;
}

// Compact element styling for markdown rendered inside a chat bubble — no
// react-markdown default spacing/sizing fits a bubble this narrow, and colors
// must inherit from the bubble (white on the user's blue, dark on assistant's grey)
// rather than being hardcoded, since the same content renders on both.
const markdownComponents = {
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="[&:not(:first-child)]:mt-2">{children}</p>
  ),
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="font-bold">{children}</strong>
  ),
  em: ({ children }: { children?: React.ReactNode }) => <em className="italic">{children}</em>,
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="mt-1 list-disc space-y-0.5 pl-4">{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="mt-1 list-decimal space-y-0.5 pl-4">{children}</ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => <li>{children}</li>,
  h1: ({ children }: { children?: React.ReactNode }) => (
    <div className="mt-2 text-[14.5px] font-bold first:mt-0">{children}</div>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <div className="mt-2 text-[14px] font-bold first:mt-0">{children}</div>
  ),
  h3: ({ children }: { children?: React.ReactNode }) => (
    <div className="mt-2 text-[13.5px] font-bold first:mt-0">{children}</div>
  ),
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} target="_blank" rel="noreferrer" className="underline">
      {children}
    </a>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code className="rounded bg-black/10 px-1 py-0.5 font-mono text-[12px]">{children}</code>
  ),
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[300px] text-[13.5px] leading-relaxed ${
          isUser
            ? "rounded-[12px_4px_12px_12px] bg-accent px-3.5 py-2.5 text-white"
            : "rounded-[4px_12px_12px_12px] bg-surface-soft px-3.5 py-2.5 text-[#1B2740]"
        }`}
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
