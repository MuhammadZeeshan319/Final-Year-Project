import { useEffect, useRef, useState } from "react";
import { rankFields } from "../api";
import { ACTIVITIES, ELECTIVES, GRADES, GRADE_FIELDS, LEVELS, OCCUPATIONS } from "../constants";
import { useEduPath } from "../context/eduPathContext";

const STEPS = [
  { title: "Your grades", hint: "Pick the option closest to your usual results in each subject.", kind: "selects", fields: GRADE_FIELDS, options: GRADES },
  { title: "Courses you have taken", hint: "How much time have you spent in each of these subjects?", kind: "selects", fields: ELECTIVES, options: LEVELS },
  { title: "Activities you take part in", hint: "Tick everything that applies. Leave all unticked if none do.", kind: "checks" },
  { title: "Your future", hint: "Think about the kind of work you can picture yourself doing.", kind: "occupation" },
];

const inputClass =
  "w-full rounded-md border border-line bg-paper px-3 py-2.5 text-ink focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-sun";

function SelectField({ id, label, value, options, onChange }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-[15px] font-medium">
        {label}
      </label>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={inputClass}>
        <option value="">Choose…</option>
        {options.map(([v, t]) => (
          <option key={v} value={v}>
            {t}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function Questionnaire() {
  const { form, setForm, setRanking, setSelectedField } = useEduPath();
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const headingRef = useRef(null);
  const cfg = STEPS[step];
  const last = step === STEPS.length - 1;

  useEffect(() => {
    headingRef.current?.focus();
  }, [step]);

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const missingCount = () => {
    if (cfg.kind === "selects") return cfg.fields.filter(([k]) => form[k] === "").length;
    if (cfg.kind === "occupation") return form.occupation === "" ? 1 : 0;
    return 0;
  };

  const next = async () => {
    const missing = missingCount();
    if (missing) {
      setError(missing === 1 ? "Please answer the highlighted question before continuing." : `Please answer all questions (${missing} left).`);
      return;
    }
    setError("");
    if (!last) return setStep(step + 1);

    setLoading(true);
    try {
      const ranking = await rankFields(form);
      setRanking(ranking);
      setSelectedField(ranking[0].field);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <p className="text-sm font-semibold text-trail">
        Step {step + 1} of {STEPS.length}
      </p>
      <div className="mt-2 mb-6 flex gap-1.5" aria-hidden="true">
        {STEPS.map((s, i) => (
          <span key={s.title} className={`h-1.5 flex-1 rounded-full ${i <= step ? "bg-trail" : "bg-line"}`} />
        ))}
      </div>

      <h1 ref={headingRef} tabIndex={-1} className="text-3xl font-extrabold tracking-tight outline-none">
        {cfg.title}
      </h1>
      <p className="mt-1 mb-6 max-w-prose text-muted">{cfg.hint}</p>

      <div className="rounded-lg border border-line bg-white p-5 sm:p-6">
        {cfg.kind === "selects" && (
          <div className="grid gap-x-5 gap-y-4 sm:grid-cols-2">
            {cfg.fields.map(([key, label]) => (
              <SelectField key={key} id={key} label={label} value={form[key]} options={cfg.options} onChange={(v) => set(key, v)} />
            ))}
          </div>
        )}

        {cfg.kind === "checks" && (
          <div className="grid gap-3 sm:grid-cols-2">
            {ACTIVITIES.map(([key, label]) => (
              <label key={key} className="flex cursor-pointer items-center gap-3 text-[15px]">
                <input type="checkbox" checked={!!form[key]} onChange={(e) => set(key, e.target.checked)} className="h-5 w-5 accent-trail" />
                {label}
              </label>
            ))}
          </div>
        )}

        {cfg.kind === "occupation" && (
          <SelectField id="occupation" label="Which kind of work can you picture yourself doing at age 30?" value={form.occupation} options={OCCUPATIONS} onChange={(v) => set("occupation", v)} />
        )}
      </div>

      <p role="alert" className="mt-3 min-h-6 font-medium text-red-700">
        {error}
      </p>

      <div className="mt-2 flex gap-3">
        {step > 0 && (
          <button
            type="button"
            onClick={() => {
              setError("");
              setStep(step - 1);
            }}
            className="rounded-md border border-trail px-5 py-2.5 font-semibold text-trail hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun"
          >
            Back
          </button>
        )}
        <button
          type="button"
          onClick={next}
          disabled={loading}
          className="rounded-md bg-trail px-6 py-2.5 font-semibold text-white hover:bg-trail-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sun disabled:cursor-wait disabled:opacity-60"
        >
          {loading ? "Ranking…" : last ? "Recommend my field" : "Next"}
        </button>
      </div>
    </div>
  );
}
