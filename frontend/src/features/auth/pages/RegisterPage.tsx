import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  User,
  Mail,
  AtSign,
  Lock,
  Eye,
  EyeOff,
  LoaderCircle,
  ArrowRight,
} from "lucide-react";

import AuthLayout from "../components/AuthLayout";
import { useAuthStore } from "../../../stores/auth.store";

export default function RegisterPage() {
  const navigate = useNavigate();

  const register = useAuthStore((state) => state.register);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);
  const clearAuthError = clearError;

  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    console.log("REGISTER FORM SUBMITTED");

    if (isSubmitting || isLoading) return;

    clearAuthError();
    setValidationError("");

    const cleanFullName = fullName.trim();
    const cleanUsername = username.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanFullName || !cleanUsername || !cleanEmail || !password) {
      setValidationError("Please complete all required fields.");
      return;
    }

    if (password.length < 8) {
      setValidationError("Password must contain at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setValidationError("Please enter a valid email address.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        full_name: cleanFullName,
        username: cleanUsername,
        email: cleanEmail,
        password,
      });

      navigate("/login", {
        replace: true,
        state: { registered: true },
      });
    } catch (registrationError) {
      console.error("Registration failed:", registrationError);
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitting = isSubmitting || isLoading;

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Set up your workspace and start reading, researching and learning."
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {(error || validationError) && (
          <div
            role="alert"
            aria-live="assertive"
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {validationError || error}
          </div>
        )}

        {/* Full name */}
        <div>
          <label htmlFor="fullName" className="form-label">
            Full name
          </label>

          <div className="relative">
            <User
              size={18}
              aria-hidden="true"
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              id="fullName"
              name="full_name"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(event) => {
                setFullName(event.target.value);
                clearAuthError();
                setValidationError("");
              }}
              placeholder="Enter your full name"
              className="form-control !pl-12"
              disabled={submitting}
              required
            />
          </div>
        </div>

        {/* Username */}
        <div>
          <label htmlFor="username" className="form-label">
            Username
          </label>

          <div className="relative">
            <AtSign
              size={18}
              aria-hidden="true"
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => {
                setUsername(event.target.value);
                clearAuthError();
                setValidationError("");
              }}
              placeholder="Choose a username"
              className="form-control !pl-12"
              disabled={submitting}
              required
            />
          </div>
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="form-label">
            Email address
          </label>

          <div className="relative">
            <Mail
              size={18}
              aria-hidden="true"
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                clearAuthError();
                setValidationError("");
              }}
              placeholder="you@example.com"
              className="form-control !pl-12"
              disabled={submitting}
              required
            />
          </div>
        </div>

        {/* Password */}
        <div>
          <label htmlFor="password" className="form-label">
            Password
          </label>

          <div className="relative">
            <Lock
              size={18}
              aria-hidden="true"
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                clearAuthError();
                setValidationError("");
              }}
              placeholder="Create a password"
              className="form-control !pl-12 !pr-12"
              disabled={submitting}
              required
            />

            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword((current) => !current)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-700"
              disabled={submitting}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <p className="caption-text mt-1">Use at least 8 characters.</p>
        </div>

        {/* Confirm password */}
        <div>
          <label htmlFor="confirmPassword" className="form-label">
            Confirm password
          </label>

          <div className="relative">
            <Lock
              size={18}
              aria-hidden="true"
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              id="confirmPassword"
              name="confirm_password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(event.target.value);
                clearAuthError();
                setValidationError("");
              }}
              placeholder="Re-enter your password"
              className="form-control !pl-12"
              disabled={submitting}
              required
            />
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting}
          className="flex min-h-[46px] w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-violet-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? (
            <>
              <LoaderCircle size={18} className="animate-spin" />
              Creating account...
            </>
          ) : (
            <>
              Create account
              <ArrowRight size={17} />
            </>
          )}
        </button>

        {/* Login link */}
        <p className="text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-violet-600 hover:text-violet-700"
          >
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
