import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Sidebar } from "../components/Sidebar";
import { getSystemPrompt, updateSystemPrompt } from "../lib/api";
import type { SystemPromptOut } from "../lib/types";

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["system-prompt"],
    queryFn: getSystemPrompt,
  });

  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (data) setDraft(data.content);
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (content: string) => updateSystemPrompt(content),
    onSuccess: (updated) => {
      // Keep the query cache in sync too, not just local draft state — otherwise
      // `data` stays stale and isDirty never clears after a successful save.
      queryClient.setQueryData<SystemPromptOut>(["system-prompt"], updated);
      setDraft(updated.content);
    },
  });

  const trimmed = draft.trim();
  const isDirty = data ? trimmed !== data.content : false;

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar />

      <div className="flex flex-1 flex-col items-center overflow-y-auto bg-surface px-8 py-10">
        <div className="w-full max-w-[640px]">
          <div className="font-display text-2xl font-bold text-ink">Tune the advisor</div>
          <div className="mt-1.5 text-sm text-muted">
            Use this to fine-tune how Koalla behaves within that role: tone, style, or
            extra rules of your own. Changes take effect on the next message, in every
            conversation.
          </div>

          {isLoading && <div className="mt-6 text-sm text-faint">Loading…</div>}
          {error && (
            <div className="mt-6 text-sm text-red-600">Couldn't load the system prompt.</div>
          )}

          {data && (
            <>
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                disabled={saveMutation.isPending}
                rows={18}
                placeholder={
                  "Add anything you'd like, for example:\n\n" +
                  "Always respond in a warm, casual tone with the occasional pun.\n" +
                  "Prefer budget-friendly suggestions unless I say otherwise.\n" +
                  "I'm vegetarian, so lean toward food recommendations that fit that.\n" +
                  "Respond in a sleepy, drowsy tone — like you're about to fall asleep."
                }
                className="mt-6 w-full rounded-xl border border-line bg-white p-4 font-mono text-[13px] leading-relaxed text-ink outline-none placeholder:text-faint focus:border-accent disabled:opacity-60"
              />

              <div className="mt-3 flex items-center gap-3">
                <button
                  type="button"
                  disabled={!isDirty || saveMutation.isPending}
                  onClick={() => saveMutation.mutate(trimmed)}
                  className="rounded-[11px] bg-accent px-4 py-2.5 text-sm font-bold text-white transition-all duration-150 hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-accent"
                >
                  {saveMutation.isPending ? "Saving…" : "Save"}
                </button>
                {saveMutation.isSuccess && !isDirty && (
                  <span className="text-[13px] text-emerald-600">Saved</span>
                )}
                {saveMutation.isError && (
                  <span className="text-[13px] text-red-600">{saveMutation.error.message}</span>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
