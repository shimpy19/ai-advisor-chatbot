// Mirrors backend/app/schemas.py — keep these in sync when the backend changes.

export interface MessageOut {
  id: string;
  role: string;
  kind: "text" | "tool_call_request" | "tool_result";
  content: string | null;
  created_at: string;
}

export interface TripDay {
  day: number;
  title?: string;
  activities?: string[];
}

export interface TripPlanOut {
  id: string;
  conversation_id: string;
  destination: string | null;
  start_date: string | null;
  end_date: string | null;
  days: TripDay[];
  updated_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface DuplicateTripOut {
  conversation_id: string;
  title: string;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  updated_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: MessageOut[];
  trip_plan: TripPlanOut | null;
  duplicate_trip: DuplicateTripOut | null;
}

export interface ChatTurnResponse {
  message: MessageOut;
  trip_plan: TripPlanOut | null;
}

export interface TripPlanUpdate {
  destination?: string;
  start_date?: string;
  end_date?: string;
  days?: TripDay[];
  remove_days?: number[];
}

export interface SystemPromptOut {
  content: string;
  updated_at: string;
}
