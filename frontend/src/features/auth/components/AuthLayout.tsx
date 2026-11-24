import { BookOpen, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import type { ReactNode } from "react";
interface AuthLayoutProps {
  children:ReactNode;
  title: string;
  subtitle: string;
}

export default function AuthLayout({
  children,
  title,
  subtitle,
}: AuthLayoutProps) {
  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-2">
      {/* Left branding panel */}
      <section className="relative hidden overflow-hidden bg-[#111827] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-violet-600/20 blur-3xl" />

        <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-indigo-500/20 blur-3xl" />

        <Link to="/" className="relative z-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-600">
            <BookOpen size={23} />
          </div>

          <div>
            <h1 className="text-lg font-bold tracking-tight">
              FLIPBOOK<span className="text-violet-400">.AI</span>
            </h1>
            <p className="text-[10px] tracking-[0.2em] text-slate-400">
              READ. LEARN. DISCOVER.
            </p>
          </div>
        </Link>

        <div className="relative z-10 max-w-lg">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-400/20 bg-violet-400/10 text-violet-300">
            <Sparkles size={23} />
          </div>

          <h2 className="text-4xl font-bold leading-tight tracking-tight xl:text-5xl">
            Your documents.
            <br />
            Your knowledge.
            <br />
            <span className="text-violet-400">Powered by AI.</span>
          </h2>

          <p className="mt-6 max-w-md text-base leading-relaxed text-slate-400">
            Transform your PDFs into interactive reading, research and learning
            experiences with FLIPBOOK-AI.
          </p>
        </div>

        <p className="relative z-10 text-xs text-slate-500">
          © {new Date().getFullYear()} FLIPBOOK-AI. All rights reserved.
        </p>
      </section>

      {/* Right form panel */}
      <section className="flex min-h-screen items-center justify-center px-5 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <Link
            to="/"
            className="mb-10 flex items-center justify-center gap-2 lg:hidden"
          >
            <BookOpen size={25} className="text-violet-600" />
            <span className="text-lg font-bold text-slate-900">
              FLIPBOOK<span className="text-violet-600">.AI</span>
            </span>
          </Link>

          <div className="mb-8">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              {title}
            </h2>

            <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
          </div>

          {children}

          <p className="mt-10 text-center text-xs text-slate-400">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </section>
    </main>
  );
}
