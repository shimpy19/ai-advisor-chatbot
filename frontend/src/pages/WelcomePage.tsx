import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { KoalaLogo } from "../components/KoalaLogo";
import { MessageComposer } from "../components/MessageComposer";
import { Sidebar } from "../components/Sidebar";
import { SplashScreen } from "../components/SplashScreen";
import { createConversation, sendMessage } from "../lib/api";

const SUGGESTIONS = [
  "Plan a week in Kyoto",
  "Find a beach escape in March",
  "Does Japan need a visa for me?",
];

export function WelcomePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showSplash, setShowSplash] = useState(true);

  const startConversationMutation = useMutation({
    mutationFn: async (content: string) => {
      const conversation = await createConversation();
      await sendMessage(conversation.id, content);
      return conversation.id;
    },
    onSuccess: (conversationId) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      navigate(`/conversations/${conversationId}`);
    },
    onError: () => {
      // createConversation() may have already succeeded even though the
      // mutation as a whole failed — invalidate so a conversation left
      // behind by a failing sendMessage() still shows up in the sidebar
      // instead of being silently orphaned.
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      {showSplash && <SplashScreen onDone={() => setShowSplash(false)} />}
      <Sidebar />

      <div className="flex flex-1 items-center justify-center bg-surface p-10">
        <div className="w-full max-w-[620px] text-center">
          <div className="mb-[18px] flex justify-center">
            <KoalaLogo size={52} />
          </div>
          <div className="font-display mb-2.5 text-[30px] font-bold text-ink">
            Where should we plan your next trip?
          </div>
          <div className="mb-7 text-[15px] leading-relaxed text-muted">
            A bit sleepy...wake me up with a good trip idea!
          </div>

          <MessageComposer
            onSend={(content) => startConversationMutation.mutate(content)}
            disabled={startConversationMutation.isPending}
            placeholder="Somewhere warm in early December, under €900…"
            className="rounded-[13px] border border-line bg-white p-1"
          />
          {startConversationMutation.isPending && (
            <div className="mt-3 text-[13px] text-faint">Setting up your trip…</div>
          )}
          {startConversationMutation.isError && (
            <div className="mt-3 text-[13px] text-red-600">
              {startConversationMutation.error.message}
            </div>
          )}

          <div className="mt-[18px] flex flex-wrap justify-center gap-2.5">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                disabled={startConversationMutation.isPending}
                onClick={() => startConversationMutation.mutate(s)}
                className="cursor-pointer rounded-full border border-line px-[15px] py-2 text-[13px] text-ink-soft transition-colors hover:border-accent hover:bg-accent-light hover:text-accent disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-line disabled:hover:bg-transparent disabled:hover:text-ink-soft"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
