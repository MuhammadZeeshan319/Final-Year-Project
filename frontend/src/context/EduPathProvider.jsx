import { useCallback, useEffect, useMemo, useState } from "react";
import { EduPathContext, SESSION_KEY, clearSession } from "./eduPathContext";
import { INITIAL_FORM } from "../constants";

function load() {
  try {
    return JSON.parse(sessionStorage.getItem(SESSION_KEY)) ?? {};
  } catch {
    return {};
  }
}

// Keeps answers and results in memory (and in sessionStorage so a page refresh doesn't lose them).
export default function EduPathProvider({ children }) {
  const [saved] = useState(load);
  const [form, setForm] = useState(saved.form ?? INITIAL_FORM);
  const [ranking, setRanking] = useState(saved.ranking ?? null);
  const [selectedField, setSelectedField] = useState(saved.selectedField ?? null);
  const [careerByField, setCareerByField] = useState(saved.careerByField ?? {});

  useEffect(() => {
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify({ form, ranking, selectedField, careerByField }));
    } catch {
      /* storage unavailable: keep working in memory */
    }
  }, [form, ranking, selectedField, careerByField]);

  const reset = useCallback(() => {
    setForm(INITIAL_FORM);
    setRanking(null);
    setSelectedField(null);
    setCareerByField({});
    clearSession();
  }, []);

  const value = useMemo(
    () => ({ form, setForm, ranking, setRanking, selectedField, setSelectedField, careerByField, setCareerByField, reset }),
    [form, ranking, selectedField, careerByField, reset],
  );

  return <EduPathContext.Provider value={value}>{children}</EduPathContext.Provider>;
}
