import { createContext, useContext } from "react";

export const EduPathContext = createContext(null);

export const SESSION_KEY = "edupath_session";
export function clearSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}

/**
 * Shared state for the whole logged-in area. Other modules can read it too, e.g.
 *   const { selectedField, ranking, form } = useEduPath();
 * selectedField = the field the student picked (one of the 15 names from the backend),
 * ranking       = [{ field, score, rank }, ...] best first,
 * form          = the student's questionnaire answers.
 */
export function useEduPath() {
  const ctx = useContext(EduPathContext);
  if (!ctx) throw new Error("useEduPath must be used inside <EduPathProvider>");
  return ctx;
}
