import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";
import { getHealth } from "./lib/api";
import { ConversationPage } from "./pages/ConversationPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WelcomePage } from "./pages/WelcomePage";

function App() {
  const { isError } = useQuery({ queryKey: ["health"], queryFn: getHealth });

  return (
    <>
      {isError && (
        <div className="bg-red-600 px-4 py-1.5 text-center text-[13px] text-white">
          Can't reach the backend right now — some features may not work.
        </div>
      )}
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/conversations/:id" element={<ConversationPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;
