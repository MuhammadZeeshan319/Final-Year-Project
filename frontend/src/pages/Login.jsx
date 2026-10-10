import { useState } from "react";
import { Link } from "react-router-dom";
import Logo from "../components/Logo";
import campusBg from "../assets/campus-bg.jpg";

const inputClass =
  "w-full h-12 rounded-xl border border-white/50 bg-white/20 px-4 text-white " +
  "placeholder-white/80 outline-none backdrop-blur-sm transition " +
  "focus:border-white focus:ring-2 focus:ring-white/40";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("Please enter a valid email address.");
      return;
    }

    setLoading(true);
    // TODO (backend phase): send { email, password } to the FastAPI login endpoint.
    console.log("Login attempt for:", email);
    setTimeout(() => setLoading(false), 800);
  };

  return (
    <div
      className="relative flex min-h-screen items-center justify-center bg-cover bg-center px-4 py-10"
      style={{ backgroundImage: `url(${campusBg})` }}
    >
      <div className="absolute inset-0 bg-black/15" />

      <div className="relative w-full max-w-[458px] rounded-3xl border border-white/45 bg-white/20 px-8 py-9 shadow-2xl backdrop-blur-md">
        <div className="flex flex-col items-center">
          <Logo />
          <span className="mt-2 text-xl font-bold text-[#1769E0]">Edu Path</span>
          <h1 className="mt-5 text-3xl font-bold text-white drop-shadow">
            Welcome Back
          </h1>
          <p className="mt-2 text-sm text-white drop-shadow">
            Sign in to continue your academic journey
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-7 space-y-4" noValidate>
          <input
            type="email"
            placeholder="Enter your email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
          <input
            type="password"
            placeholder="Enter your password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />

          {error && (
            <p className="rounded-lg bg-red-500/80 px-3 py-2 text-sm text-white">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="h-12 w-full rounded-xl bg-[#1769E0] font-semibold text-white transition hover:bg-[#1259c4] disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <div className="mt-5 text-center text-sm text-white drop-shadow">
          <a href="#" className="font-medium text-sky-200 hover:underline">
            Forgot Password?
          </a>
          <p className="mt-3">
            Don't have an account?{" "}
            <Link to="/signup" className="font-semibold text-sky-200 hover:underline">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}