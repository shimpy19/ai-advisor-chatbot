import type { TripPlanOut } from "../lib/types";

interface TripPlanPlaceholderProps {
  tripPlan: TripPlanOut | null;
}

// Minimal placeholder for sub-task 2 — sub-task 3 replaces this with the full,
// editable day-by-day trip plan view.
export function TripPlanPlaceholder({ tripPlan }: TripPlanPlaceholderProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-surface px-8 text-center">
      {tripPlan ? (
        <>
          <div className="font-display text-2xl font-bold text-ink">
            {tripPlan.destination ?? "Trip plan"}
          </div>
          {(tripPlan.start_date || tripPlan.end_date) && (
            <div className="mt-1 text-sm text-muted">
              {tripPlan.start_date ?? "?"} – {tripPlan.end_date ?? "?"}
            </div>
          )}
          <div className="mt-4 text-sm text-faint">
            {tripPlan.days.length} day{tripPlan.days.length === 1 ? "" : "s"} planned so far — full
            trip plan view coming soon.
          </div>
        </>
      ) : (
        <div className="text-sm text-faint">
          No trip plan yet — keep chatting and it'll take shape here.
        </div>
      )}
    </div>
  );
}
