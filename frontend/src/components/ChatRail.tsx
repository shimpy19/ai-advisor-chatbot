import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { sendMessage } from "../lib/api";
import type { ConversationDetail } from "../lib/types";
import { DuplicateTripNotice } from "./DuplicateTripNotice";
import { MessageBubble } from "./MessageBubble";
import { MessageComposer } from "./MessageComposer";

interface ChatRailProps {
  conversation: ConversationDetail;
}

export function ChatRail({ conversation }: ChatRailProps) {
  const [open, setOpen] = useState(true);
  const queryClient = useQueryClient();
  const bottomRef = useRef<HTMLDivElement>(null);

  const visibleMessages = conversation.messages.filter((m) => m.kind === "text");

  const sendMutation = useMutation({
    mutationFn: (content: string) => sendMessage(conversation.id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", conversation.id] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: () => {
      // The user's message is persisted server-side before the LLM call
      // can fail, so refetch to surface it instead of leaving it invisible.
      queryClient.invalidateQueries({ queryKey: ["conversation", conversation.id] });
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation.id, visibleMessages.length, sendMutation.isPending]);

  if (!open) {
    return (
      <div className="flex w-14 shrink-0 flex-col items-center gap-2.5 border-r border-line bg-white pt-[18px]">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open chat"
          className="flex items-center justify-center rounded-[10px] bg-accent-light p-2.5 text-accent"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className="flex w-[380px] shrink-0 flex-col border-r border-line bg-white">
      <div className="flex h-[58px] shrink-0 items-center justify-between border-b border-line px-[18px]">
        <div className="text-[13px] font-bold tracking-wide text-ink-soft">Chat</div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Collapse chat"
          className="p-1 text-[#8A97AE]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-[18px]">
        {visibleMessages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {sendMutation.isPending && sendMutation.variables && (
          <MessageBubble
            message={{
              id: "pending",
              role: "user",
              kind: "text",
              content: sendMutation.variables,
              created_at: new Date().toISOString(),
            }}
          />
        )}
        {sendMutation.isPending && (
          <div className="flex justify-start">
            <div className="rounded-[4px_12px_12px_12px] bg-surface-soft px-3.5 py-2.5 text-[13.5px] text-faint">
              Thinking…
            </div>
          </div>
        )}
        {sendMutation.isError && (
          <div className="rounded-lg bg-red-50 px-3.5 py-2.5 text-[13px] text-red-600">
            {sendMutation.error.message}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="relative shrink-0 border-t border-line p-3">
        {conversation.duplicate_trip && (
          <DuplicateTripNotice
            key={conversation.duplicate_trip.conversation_id}
            conversationId={conversation.id}
            duplicate={conversation.duplicate_trip}
          />
        )}
        <MessageComposer
          onSend={(content) => sendMutation.mutate(content)}
          disabled={sendMutation.isPending}
        />
      </div>
    </div>
  );
}
