import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateTripPlan } from "../lib/api";
import type { ConversationDetail, TripDay, TripPlanOut, TripPlanUpdate } from "../lib/types";
import { EditableText } from "./EditableText";

interface TripPlanPanelProps {
  conversationId: string;
  tripPlan: TripPlanOut | null;
}

function activitiesToText(activities?: string[]): string {
  return (activities ?? []).join("\n");
}

function textToActivities(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function TripPlanPanel({ conversationId, tripPlan }: TripPlanPanelProps) {
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (update: TripPlanUpdate) => updateTripPlan(conversationId, update),
    onSuccess: (trip_plan) => {
      // The response already is the complete, fresh trip_plan — patch it directly
      // instead of invalidating and refetching the whole conversation (messages
      // included) just to reflect one field's change.
      queryClient.setQueryData<ConversationDetail>(["conversation", conversationId], (old) =>
        old ? { ...old, trip_plan } : old,
      );
    },
  });

  const days: TripDay[] = tripPlan?.days ?? [];

  function saveDayField(day: TripDay, patch: Partial<TripDay>) {
    // Send only the changed field(s), not the rest of `day` — the backend now
    // merges per-field, so this can't clobber a concurrent edit to another field
    // of the same day using a stale cached snapshot.
    updateMutation.mutate({ days: [{ day: day.day, ...patch }] });
  }

  function addDay() {
    const nextDay = days.length ? Math.max(...days.map((d) => d.day)) + 1 : 1;
    updateMutation.mutate({ days: [{ day: nextDay, title: "", activities: [] }] });
  }

  function removeDay(day: number) {
    if (window.confirm(`Remove day ${day}? Later days will be renumbered.`)) {
      updateMutation.mutate({ remove_days: [day] });
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto bg-surface px-8 py-7">
      <div className="mx-auto w-full max-w-[520px]">
        <EditableText
          value={tripPlan?.destination ?? ""}
          placeholder="Click to set destination"
          onSave={(destination) => updateMutation.mutate({ destination })}
          className="font-display block text-2xl font-bold text-ink"
          inputClassName="font-display block w-full rounded-lg border border-line bg-white px-2 py-1 text-2xl font-bold text-ink outline-none"
        />

        <div className="mt-1.5 flex items-center gap-1.5 text-sm text-muted">
          <EditableText
            value={tripPlan?.start_date ?? ""}
            placeholder="start date"
            onSave={(start_date) => updateMutation.mutate({ start_date })}
            inputClassName="w-28 rounded-md border border-line bg-white px-1.5 py-0.5 text-sm outline-none"
          />
          <span>–</span>
          <EditableText
            value={tripPlan?.end_date ?? ""}
            placeholder="end date"
            onSave={(end_date) => updateMutation.mutate({ end_date })}
            inputClassName="w-28 rounded-md border border-line bg-white px-1.5 py-0.5 text-sm outline-none"
          />
        </div>

        {!tripPlan && (
          <div className="mt-3 text-[13px] text-faint">
            No trip plan yet — keep chatting and it'll take shape here, or set the basics
            yourself below.
          </div>
        )}

        {updateMutation.isError && (
          <div className="mt-3 rounded-lg bg-red-50 px-3.5 py-2.5 text-[13px] text-red-600">
            {updateMutation.error.message}
          </div>
        )}

        <div className="mt-6 flex flex-col gap-3">
          {days.length === 0 && (
            <div className="text-sm text-faint">No days planned yet.</div>
          )}
          {days.map((day) => (
            <div key={day.day} className="rounded-xl border border-line bg-white p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="text-[11px] font-bold uppercase tracking-wide text-faint">
                  Day {day.day}
                </div>
                <button
                  type="button"
                  aria-label={`Remove day ${day.day}`}
                  onClick={() => removeDay(day.day)}
                  className="text-[11px] font-semibold text-faint hover:text-red-600"
                >
                  Remove
                </button>
              </div>
              <EditableText
                value={day.title ?? ""}
                placeholder="Click to add a title"
                onSave={(title) => saveDayField(day, { title })}
                className="mt-1 block text-[15px] font-semibold text-ink"
                inputClassName="mt-1 block w-full rounded-md border border-line bg-white px-2 py-1 text-[15px] font-semibold text-ink outline-none"
              />
              <EditableText
                value={activitiesToText(day.activities)}
                placeholder="Click to add activities, one per line"
                onSave={(text) => saveDayField(day, { activities: textToActivities(text) })}
                multiline
                className="mt-1.5 block whitespace-pre-wrap text-[13.5px] leading-relaxed text-ink-soft"
                inputClassName="mt-1.5 block w-full rounded-md border border-line bg-white px-2 py-1 text-[13.5px] leading-relaxed text-ink-soft outline-none"
              />
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={addDay}
          disabled={updateMutation.isPending}
          className="mt-3 w-full rounded-xl border border-dashed border-line py-2.5 text-[13px] font-semibold text-muted hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-line disabled:hover:text-muted"
        >
          + Add day
        </button>
      </div>
    </div>
  );
}
