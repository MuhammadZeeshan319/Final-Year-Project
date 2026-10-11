// Calls the Flask backend (proxied through Vite at /api, see vite.config.js).
async function request(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch {
    throw new Error("Cannot reach the EduPath server. Make sure the backend is running (python app.py in the backend folder).");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

const json = (body) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

/** Student form answers -> [{field, score, rank}, ...] for all 15 fields, best first. */
export const rankFields = (form) => request("/api/rank", json(form)).then((d) => d.ranking);

/** Field name -> its 3 follow-up questions. */
export const getCareerQuestions = (field) =>
  request(`/api/career-questions?field=${encodeURIComponent(field)}`).then((d) => d.questions);

/** Field + answers -> {title, description, why} (hard-coded if/else rules, no ML). */
export const getCareer = (field, answers) => request("/api/career", json({ field, answers }));
