import { useQuery } from "@tanstack/react-query";
import { getHealth } from "./lib/api";

function App() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <h1 className="font-display text-2xl font-semibold text-slate-900">
          AI Travel Advisor
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Frontend scaffold — sub-task 1 placeholder
        </p>

        <div className="mt-6 rounded-lg bg-slate-100 px-4 py-3 text-sm">
          {isLoading && <span className="text-slate-500">Checking backend connection…</span>}
          {error && (
            <span className="text-red-600">
              Could not reach the backend: {error.message}
            </span>
          )}
          {data && (
            <span className="text-emerald-600">
              Backend connected — status: {data.status}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
