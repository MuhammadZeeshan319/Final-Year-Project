import { useEduPath } from "../context/eduPathContext";

// Placeholder page for modules other team members are building. They can read the student's data with
// useEduPath(): selectedField, ranking, form (see context/eduPathContext.js).
export default function ComingSoon({ title, description }) {
  const { selectedField } = useEduPath();
  return (
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">{title}</h1>
      <p className="mt-1 mb-6 max-w-prose text-muted">{description}</p>
      <div className="rounded-lg border border-dashed border-trail bg-white p-6">
        <p className="font-semibold">This feature is coming soon.</p>
        <p className="mt-1 text-muted">
          It will start from the field you selected: <strong className="text-ink">{selectedField}</strong>.
        </p>
      </div>
    </div>
  );
}
