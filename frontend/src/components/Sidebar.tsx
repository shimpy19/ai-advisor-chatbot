import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { deleteConversation, listConversations, renameConversation } from "../lib/api";
import { formatRelativeTime } from "../lib/format";
import { EditableText } from "./EditableText";
import { KoalaLogo } from "./KoalaLogo";

export function Sidebar() {
  const { id: activeId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [renamingId, setRenamingId] = useState<string | null>(null);

  const { data: conversations, error } = useQuery({
    queryKey: ["conversations"],
    queryFn: listConversations,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_data, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      if (deletedId === activeId) navigate("/");
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => renameConversation(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  function handleDelete(e: React.MouseEvent, id: string, title: string) {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm(`Delete "${title}"? This can't be undone.`)) {
      deleteMutation.mutate(id);
    }
  }

  function startRename(e: React.MouseEvent, id: string) {
    e.preventDefault();
    e.stopPropagation();
    setRenamingId(id);
  }

  return (
    <div className="flex w-[264px] shrink-0 flex-col border-r border-line bg-surface-soft py-[22px]">
      <div className="flex items-center gap-2.5 px-5 pb-[18px]">
        <KoalaLogo />
        <div>
          <div className="font-display text-[17px] font-bold leading-tight text-ink">Koalla</div>
          <div className="text-[11px] tracking-wide text-faint">AI travel advisor</div>
        </div>
      </div>

      <div className="px-4 pb-3.5">
        <Link
          to="/"
          className="flex w-full items-center justify-center gap-2 rounded-[11px] bg-accent px-3.5 py-2.5 text-sm font-bold text-white transition-all duration-150 hover:bg-[#1d4ed8] hover:shadow-md active:scale-[0.98]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New conversation
        </Link>
      </div>

      <div className="px-3 pb-2 text-[11px] font-bold uppercase tracking-wide text-faint">
        Conversations
      </div>

      <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2.5">
        {error && (
          <div className="px-3 py-4 text-center text-[13px] leading-relaxed text-red-600">
            Couldn't load conversations.
          </div>
        )}
        {!error && conversations?.length === 0 && (
          <div className="px-3 py-4 text-center text-[13px] leading-relaxed text-faint">
            No conversations yet. Start one and it'll show up here.
          </div>
        )}
        {conversations?.map((c) => (
          <Link
            key={c.id}
            to={`/conversations/${c.id}`}
            className={`group flex items-center justify-between gap-2 rounded-[9px] px-2.5 py-2.5 ${
              c.id === activeId ? "bg-accent-light" : "hover:bg-accent-light/50"
            }`}
          >
            <div className="min-w-0 flex-1">
              <EditableText
                value={c.title}
                editing={renamingId === c.id}
                onEditingChange={(editing) => setRenamingId(editing ? c.id : null)}
                onSave={(title) => {
                  const trimmed = title.trim();
                  if (trimmed && trimmed !== c.title) {
                    renameMutation.mutate({ id: c.id, title: trimmed });
                  }
                }}
                className="block truncate text-[13.5px] font-semibold text-[#17223B]"
                inputClassName="w-full rounded-md border border-line bg-white px-1.5 py-0.5 text-[13.5px] font-semibold text-[#17223B] outline-none"
              />
              <div className="mt-0.5 text-[11.5px] text-[#8A97AE]">{formatRelativeTime(c.updated_at)}</div>
            </div>
            <div className="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100">
              <button
                type="button"
                aria-label={`Rename ${c.title}`}
                onClick={(e) => startRename(e, c.id)}
                className="rounded-md p-1 text-[#9AA6BD] hover:bg-white"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z" />
                </svg>
              </button>
              <button
                type="button"
                aria-label={`Delete ${c.title}`}
                onClick={(e) => handleDelete(e, c.id, c.title)}
                className="rounded-md p-1 text-[#9AA6BD] hover:bg-white"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                  <path d="M10 11v6" />
                  <path d="M14 11v6" />
                  <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                </svg>
              </button>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-2.5 border-t border-line px-4 pt-3">
        <Link
          to="/settings"
          className="flex items-center gap-2.5 rounded-lg px-1.5 py-2.5 text-[13px] font-semibold text-ink-soft"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          Tune the advisor
        </Link>
      </div>
    </div>
  );
}
