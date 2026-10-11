import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import EduPathProvider from "./context/EduPathProvider";
import AppShell from "./components/AppShell";
import FieldPage from "./pages/FieldPage";
import CareerPage from "./pages/CareerPage";
import ComingSoon from "./pages/ComingSoon";
import { FEATURES } from "./constants";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />

      {/* Inside the website: questions -> field recommendation -> features on the left */}
      <Route
        path="/app"
        element={
          <EduPathProvider>
            <AppShell />
          </EduPathProvider>
        }
      >
        <Route index element={<FieldPage />} />
        <Route path="careers" element={<CareerPage />} />
        {/* Placeholders for the other modules (program recommendation, ranking, ...) */}
        {FEATURES.filter((f) => f.status === "soon").map((f) => (
          <Route key={f.to} path={f.to.replace("/app/", "")} element={<ComingSoon title={f.label} description={f.description} />} />
        ))}
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Route>

      {/* Next phases: /signup and /confirm-email */}
    </Routes>
  );
}
