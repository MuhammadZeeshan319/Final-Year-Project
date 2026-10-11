import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getCareer, getCareerQuestions } from "../api";
import { useEduPath } from "../context/eduPathContext";

// /app/careers : 3 follow-up questions for the selected field -> one specific career.
// The career itself comes from hard-coded if/else rules on the backend (careers.py), no ML.
export default function CareerPage() {
  const { ranking, selectedField, setSelectedField } = useEduPath();
  if (!selectedField) return <Navigate to="/app" replace />;

  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Career guidance</h1>
      <p className="mt-1 mb-5 max-w-prose text-muted">A few more questions will narrow your field down to one specific career.</p>

      <div className="mb-6">
        <label htmlFor="field" className="mb-1.5 block text-[15px] font-medium">
          Field
        </label>
        <select
          id="field"
          value={selectedField}
          onChange={(e) => setSelectedField(e.target.value)}
          className="w-full max-w-md rounded-md border border-line bg-white px-3 py-2.5 font-semibold focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-sun"
        >
          {ranking.map((r) => (
            <option key={r.field} value={r.field}>
              #{r.rank} {r.field} ({r.score}%)
            </option>
          ))}
        </select>
      </div>

      {/* key = field, so switching field gives a fresh set of questions */}
      <CareerFlow key={selectedField} field={selectedField} />
    </div>
  );
}

function CareerFlow({ field }) {
  const { careerByField, setCareerByField } = useEduPath();
  const saved = careerByField[field];

  const [questions, setQuestions] = useState(null);
  const [picks, setPicks] = useState(saved?.answers ?? {});
  const [result, setResult] = useState(saved?.result ?? null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getCareerQuestions(field)
      .then((q) => !cancelled && setQuestions(q))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [field]);

  const submit = async () => {
    if (questions.some((q) => !picks[q.id])) {
      setError("Please answer all the questions.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const r = await getCareer(field, picks);
      setResult(r);
      setCareerByField((m) => ({ ...m, [field]: { answers: picks, result: r } }));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const retry = () => {
    setResult(null);
    setPicks({});
    setCareerByField((m) => Object.fromEntries(Object.entries(m).filter(([f]) => f !== field)));
  };

  return (
    <>
      {!questions && !error && <p className="text-muted">Loading questions…</p>}

      {questions && !result && (
        <>
          {questions.map((q, i) => (
            <fieldset key={q.id} className="mb-4 rounded-lg border border-line bg-white p-5">
              <legend className="px-1 text-lg font-bold">
                {i + 1}. {q.text}
              </legend>
              <div className="mt-2 space-y-1">
                {q.options.map((o) => (
                  <label key={o.value} className="flex cursor-pointer items-start gap-3 rounded-md px-2 py-2 hover:bg-paper">
                    <input
                      type="radio"
                      name={q.id}
                      value={o.value}
                      checked={picks[q.id] === o.value}
                      onChange={() => setPicks((p) => ({ ...p, [q.id]: o.value }))}
                      className="mt-1 h-4 w-4 accent-trail"
                    />
                    <span>{o.label}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className="rounded-md bg-trail px-6 py-2.5 font-semibold text-white hover:bg-trail-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun disabled:cursor-wait disabled:opacity-60"
          >
            {loading ? "Finding…" : "Show my career"}
          </button>
        </>
      )}

      <p role="alert" className="mt-3 min-h-6 font-medium text-red-700">
        {error}
      </p>

      {result && (
        <section aria-live="polite" className="rounded-lg border-2 border-sun bg-sun-soft p-6">
          <p className="text-sm font-semibold tracking-wide text-muted uppercase">Recommended career in {field}</p>
          <h2 className="mt-1 text-3xl leading-tight font-extrabold tracking-tight">{result.title}</h2>
          <p className="mt-3 max-w-prose">{result.description}</p>
          <p className="mt-3 max-w-prose text-sm text-muted">{result.why}</p>
          <button
            type="button"
            onClick={retry}
            className="mt-5 rounded-md border border-trail bg-white px-5 py-2.5 font-semibold text-trail hover:bg-paper focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun"
          >
            Try different answers
          </button>
        </section>
      )}
    </>
  );
}
