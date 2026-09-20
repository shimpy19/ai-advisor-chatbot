import type {
  ChatTurnResponse,
  ConversationDetail,
  ConversationSummary,
  TripPlanOut,
  TripPlanUpdate,
} from "./types";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // response wasn't JSON — fall back to the status-based message above
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function getHealth(): Promise<{ status: string }> {
  return apiFetch("/health");
}

export async function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch("/conversations");
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch(`/conversations/${id}`);
}

export async function createConversation(title?: string): Promise<ConversationDetail> {
  return apiFetch("/conversations", {
    method: "POST",
    body: JSON.stringify(title ? { title } : {}),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  return apiFetch(`/conversations/${id}`, { method: "DELETE" });
}

export async function sendMessage(id: string, content: string): Promise<ChatTurnResponse> {
  return apiFetch(`/conversations/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function renameConversation(id: string, title: string): Promise<ConversationDetail> {
  return apiFetch(`/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export async function updateTripPlan(id: string, update: TripPlanUpdate): Promise<TripPlanOut> {
  return apiFetch(`/conversations/${id}/trip-plan`, {
    method: "PATCH",
    body: JSON.stringify(update),
  });
}
