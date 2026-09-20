import { Link } from "react-router-dom";

// Placeholder — sub-task 4 replaces this with the real system-prompt editor.
export function SettingsPage() {
  return (
    <div className="flex h-screen items-center justify-center bg-surface">
      <div className="text-center">
        <div className="font-display text-xl font-semibold text-ink">Advisor settings</div>
        <div className="mt-2 text-sm text-faint">Coming in sub-task 4.</div>
        <Link to="/" className="mt-4 inline-block text-sm font-semibold text-accent">
          Back to chat
        </Link>
      </div>
    </div>
  );
}
