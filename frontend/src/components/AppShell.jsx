import { useState } from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import Sidebar from "./Sidebar";
import { clearSession, useEduPath } from "../context/eduPathContext";

export default function AppShell() {
  const { ranking } = useEduPath();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  // Until a field has been recommended, only the questions page is available.
  if (!ranking && pathname.replace(/\/$/, "") !== "/app") return <Navigate to="/app" replace />;

  const logout = () => {
    // Forget the saved answers; the in-memory state disappears when we leave /app.
    clearSession();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <header className="sticky top-0 z-50 flex h-14 items-center justify-between border-b border-line bg-white px-4 sm:px-6">
        <div className="flex items-center gap-3">
          {ranking && (
            <button
              type="button"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Toggle features menu"
              aria-expanded={menuOpen}
              className="rounded-md border border-line px-2.5 py-1.5 text-sm font-semibold lg:hidden"
            >
              Menu
            </button>
          )}
          <span className="text-xl font-extrabold tracking-tight">
            Edu<span className="text-trail">Path</span>
          </span>
        </div>
        <button
          type="button"
          onClick={logout}
          className="rounded-md px-3 py-1.5 text-sm font-semibold text-trail hover:bg-paper focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun"
        >
          Log out
        </button>
      </header>

      <div className="flex flex-1">
        {ranking && <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />}
        <main className="min-w-0 flex-1 px-4 py-8 sm:px-8">
          <div className={`max-w-3xl ${ranking ? "" : "mx-auto"}`}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
