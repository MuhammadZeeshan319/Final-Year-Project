// ============================================================================
// PLACEHOLDER LOGIN -- REPLACE WITH YOUR TEAM'S REAL src/pages/Login.jsx.
// (This file only exists so the project runs on its own. When merging, KEEP
// your own Login.jsx and don't copy this one.)
//
// All the real Login has to do for the new flow: after a successful login, call
//     const navigate = useNavigate();   ...   navigate("/app");
// ============================================================================
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSubmit = (e) => {
    e.preventDefault();
    navigate("/app");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-8 shadow">
        <h1 className="text-2xl font-bold">Log in to EduPath</h1>
        <p className="text-sm text-gray-500">Placeholder login: replace with your team's page.</p>
        <label className="block text-sm font-medium">
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full rounded border border-gray-300 px-3 py-2" />
        </label>
        <label className="block text-sm font-medium">
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 w-full rounded border border-gray-300 px-3 py-2" />
        </label>
        <button type="submit" className="w-full rounded bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700">
          Login
        </button>
      </form>
    </div>
  );
}
