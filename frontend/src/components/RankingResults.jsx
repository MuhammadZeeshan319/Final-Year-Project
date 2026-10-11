import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useEduPath } from "../context/eduPathContext";

export default function RankingResults() {
  const { ranking, selectedField, setSelectedField, setRanking } = useEduPath();
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setAnimate(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const max = Math.max(...ranking.map((r) => r.score));
  const visible = showAll ? ranking : ranking.slice(0, 6);

  const choose = (field) => {
    setSelectedField(field);
    navigate("/app/careers");
  };

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Fields that fit your profile</h1>
      <p className="mt-1 mb-6 max-w-prose text-muted">
        Your top match is <strong className="text-ink">{ranking[0].field}</strong>. Select any field to get a specific career for it. The features
        for your chosen field are now in the menu on the left.
      </p>

      <ol className="mb-5 space-y-2.5">
        {visible.map((r) => (
          <li key={r.field} className={`relative overflow-hidden rounded-lg border bg-white ${r.rank === 1 ? "border-sun" : "border-line"}`}>
            <span
              aria-hidden="true"
              className={`absolute inset-y-0 left-0 transition-[width] duration-700 ease-out motion-reduce:transition-none ${r.rank === 1 ? "bg-sun-soft" : "bg-bar"}`}
              style={{ width: animate ? `${(r.score / max) * 100}%` : "0%" }}
            />
            <button
              type="button"
              onClick={() => choose(r.field)}
              aria-current={r.field === selectedField ? "true" : undefined}
              className="relative z-10 flex w-full cursor-pointer items-center justify-between gap-4 px-4 py-3.5 text-left focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sun"
            >
              <span>
                <span className="mr-2.5 text-sm text-muted">#{r.rank}</span>
                <span className="text-lg font-bold">{r.field}</span>
                {r.field === selectedField && <span className="ml-2 rounded-full bg-trail px-2 py-0.5 align-middle text-xs font-semibold text-white">Selected</span>}
              </span>
              <span className="font-semibold whitespace-nowrap">{r.score}%</span>
            </button>
          </li>
        ))}
      </ol>

      <p className="mb-5 max-w-prose text-sm text-muted">
        These percentages are the model's relative scores across all {ranking.length} fields, not guarantees. Predicting a future field of study from
        school data is hard, so use this as a starting point for exploring.
      </p>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setShowAll((s) => !s)}
          className="rounded-md border border-trail px-5 py-2.5 font-semibold text-trail hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun"
        >
          {showAll ? "Show top 6 only" : `Show all ${ranking.length} fields`}
        </button>
        <button
          type="button"
          onClick={() => setRanking(null)}
          className="rounded-md border border-line px-5 py-2.5 font-semibold hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun"
        >
          Change my answers
        </button>
      </div>
    </div>
  );
}
