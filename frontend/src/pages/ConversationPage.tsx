import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ChatRail } from "../components/ChatRail";
import { Sidebar } from "../components/Sidebar";
import { TripPlanPlaceholder } from "../components/TripPlanPlaceholder";
import { getConversation } from "../lib/api";

export function ConversationPage() {
  const { id } = useParams<{ id: string }>();

  const { data: conversation, isLoading, error } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => getConversation(id!),
    enabled: !!id,
  });

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar />

      {isLoading && (
        <div className="flex flex-1 items-center justify-center text-sm text-faint">
          Loading conversation…
        </div>
      )}

      {error && (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
          <div className="text-sm text-red-600">{error.message}</div>
          <Link to="/" className="text-sm font-semibold text-accent">
            Start a new conversation
          </Link>
        </div>
      )}

      {conversation && (
        <>
          <ChatRail conversation={conversation} />
          <TripPlanPlaceholder tripPlan={conversation.trip_plan} />
        </>
      )}
    </div>
  );
}
