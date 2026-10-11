import { NavLink } from "react-router-dom";
import { FEATURES } from "../constants";
import { useEduPath } from "../context/eduPathContext";

// Appears on the left once a field has been recommended.
export default function Sidebar({ open, onClose }) {
  const { ranking, selectedField, setRanking } = useEduPath();
  const current = ranking?.find((r) => r.field === selectedField);

  return (
    <>
      {open && <div className="fixed inset-0 top-14 z-30 bg-ink/40 lg:hidden" onClick={onClose} aria-hidden="true" />}
      <aside
        aria-label="Features"
        className={`fixed top-14 bottom-0 left-0 z-40 w-72 overflow-y-auto border-r border-line bg-white p-5 transition-transform lg:sticky lg:z-10 lg:h-[calc(100vh-3.5rem)] lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-6 rounded-lg border-2 border-sun bg-sun-soft p-4">
          <p className="text-xs font-semibold tracking-wide text-muted uppercase">Selected field</p>
          <p className="mt-1 text-lg leading-snug font-bold text-ink">{selectedField}</p>
          {current && <p className="mt-1 text-sm text-muted">Model score: {current.score}%</p>}
          <NavLink to="/app" end onClick={onClose} className="mt-3 inline-block text-sm font-semibold text-trail underline">
            Change field
          </NavLink>
        </div>

        <nav>
          <ul className="space-y-1">
            {FEATURES.map((f) => (
              <li key={f.to}>
                <NavLink
                  to={f.to}
                  end={f.end}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between rounded-md border-l-4 px-3 py-2.5 text-[15px] ${
                      isActive
                        ? "border-sun bg-sun-soft font-semibold text-ink"
                        : "border-transparent text-ink hover:bg-paper"
                    }`
                  }
                >
                  <span>{f.label}</span>
                  {f.status === "soon" && (
                    <span className="rounded-full bg-paper px-2 py-0.5 text-xs font-medium text-muted">Soon</span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <button
          type="button"
          onClick={() => setRanking(null)}
          className="mt-8 w-full rounded-md border border-trail px-3 py-2 text-sm font-semibold text-trail hover:bg-paper focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun"
        >
          Change my answers
        </button>
      </aside>
    </>
  );
}
