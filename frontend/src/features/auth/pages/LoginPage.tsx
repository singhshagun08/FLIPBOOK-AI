import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, LoaderCircle, ArrowRight, Mail } from "lucide-react";

import AuthLayout from "../components/AuthLayout";
import { useAuthStore } from "../../../stores/auth.store";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState("");

  const redirectPath = location.state?.from?.pathname || "/";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    clearError();
    setValidationError("");

    if (!identifier.trim() || !password) {
      setValidationError("Please enter your username/email and password.");
      return;
    }

    try {
      await login({
        identifier: identifier.trim(),
        password,
      });

      navigate(redirectPath, { replace: true });
    } catch {
      // The authentication store handles the backend error.
    }
  };

  return (
    <AuthLayout
      title="Welcome"
      subtitle="Sign in to continue to your FLIPBOOK-AI workspace."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {(error || validationError) && (
          <div
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {validationError || error}
          </div>
        )}

        <div>
          <label htmlFor="identifier" className="form-label">
            Username or email
          </label>

          <div className="relative">
            <Mail
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              id="identifier"
              name="identifier"
              type="text"
              autoComplete="username"
              value={identifier}
              onChange={(event) => {
                setIdentifier(event.target.value);
                clearError();
                setValidationError("");
              }}
              placeholder="Enter your username or email"
              className="form-control !pl-10"
              disabled={isLoading}
              required
            />
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <label htmlFor="password" className="form-label mb-0">
              Password
            </label>

            <span className="text-xs text-slate-400">Forgot password?</span>
          </div>

          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                clearError();
                setValidationError("");
              }}
              placeholder="Enter your password"
              className="form-control pr-12"
              disabled={isLoading}
              required
            />

            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword((current) => !current)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex min-h-[46px] w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? (
            <>
              <LoaderCircle size={18} className="animate-spin" />
              Signing in...
            </>
          ) : (
            <>
              Sign in
              <ArrowRight size={17} />
            </>
          )}
        </button>

        <p className="text-center text-sm text-slate-500">
          Don't have an account?{" "}
          <Link
            to="/register"
            className="font-semibold text-violet-600 hover:text-violet-700"
          >
            Create account
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
