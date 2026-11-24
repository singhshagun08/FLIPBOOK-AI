import type { ElementType } from "react";

import { BrowserRouter, Navigate, Route, Routes, Link } from "react-router-dom";

import AppLayout from "../components/layout/AppLayout";
import Footer from "../components/layout/Footer";
import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";

import PDFReaderPage from "../features/reader/pages/PDFReaderPage";
import LoginPage from "../features/auth/pages/LoginPage";
import RegisterPage from "../features/auth/pages/RegisterPage";
import LibraryPage from "../features/library/pages/LibraryPage";
import AssistantPage from "../features/assistant/AssistantPage";

import LearningPage from "../features/learning/pages/LearningPage";
import QuizTakingPage from "../features/learning/pages/QuizTakingPage";
import QuizResultsPage from "../features/learning/pages/QuizResultsPage";

import {
  BookOpen,
  Library,
  MessageSquareText,
  FlaskConical,
  NotebookPen,
  Headphones,
  Languages,
  ChartNoAxesCombined,
  Settings,
  Upload,
  Sparkles,
} from "lucide-react";

// ---------------------------------------------
// Placeholder Page
// ---------------------------------------------

type PlaceholderPageProps = {
  title: string;
  description: string;
  icon: ElementType;
};

function PlaceholderPage({
  title,
  description,
  icon: Icon,
}: PlaceholderPageProps) {
  return (
    <section className="space-y-6">
      <div className="page-header">
        <div>
          <h2 className="heading-2 text-slate-900">{title}</h2>
          <p className="body-text mt-1">{description}</p>
        </div>
      </div>

      <div className="flex min-h-[360px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-50 text-violet-600">
          <Icon size={30} strokeWidth={1.7} />
        </div>

        <h3 className="text-lg font-semibold text-slate-900">
          {title} workspace
        </h3>

        <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-500">
          This section is ready for development. We will connect its interface
          and functionality to the FLIPBOOK-AI backend in the next stages.
        </p>

        <div className="mt-6 flex items-center gap-2 rounded-full bg-violet-50 px-4 py-2 text-xs font-medium text-violet-700">
          <Sparkles size={14} />
          Coming in the feature implementation phase
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------
// Dashboard Page
// ---------------------------------------------

function DashboardPage() {
  const quickActions = [
    {
      title: "Upload a document",
      description: "Add a PDF to your personal library.",
      icon: Upload,
      path: "/library",
    },
    {
      title: "Open AI Assistant",
      description: "Explore AI-powered document conversations.",
      icon: MessageSquareText,
      path: "/assistant",
    },
    {
      title: "Start reading",
      description: "Open your interactive reading workspace.",
      icon: BookOpen,
      path: "/reader",
    },
  ];

  const statistics = [
    {
      label: "Total Documents",
      value: "0",
      icon: Library,
    },
    {
      label: "Reading Sessions",
      value: "0",
      icon: BookOpen,
    },
    {
      label: "AI Conversations",
      value: "0",
      icon: MessageSquareText,
    },
    {
      label: "Research Notes",
      value: "0",
      icon: NotebookPen,
    },
  ];

  return (
    <section className="space-y-8">
      <div className="page-header">
        <div>
          <p className="mb-2 text-sm font-medium text-violet-600">
            YOUR PERSONAL KNOWLEDGE SPACE
          </p>

          <h2 className="heading-1 text-slate-900">Welcome to FLIPBOOK-AI</h2>

          <p className="body-text mt-2 max-w-2xl">
            Read documents, explore ideas and turn information into knowledge
            with your AI-powered workspace.
          </p>
        </div>

        <div className="hidden items-center gap-2 rounded-xl border border-violet-100 bg-violet-50 px-4 py-3 text-sm font-medium text-violet-700 sm:flex">
          <Sparkles size={17} />
          AI-powered workspace
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statistics.map((stat) => {
          const Icon = stat.icon;

          return (
            <div
              key={stat.label}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-slate-500">{stat.label}</p>

                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                  <Icon size={18} />
                </div>
              </div>

              <p className="text-2xl font-bold tracking-tight text-slate-900">
                {stat.value}
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Your activity will appear here
              </p>
            </div>
          );
        })}
      </div>

      <div>
        <div className="mb-4">
          <h3 className="heading-3 text-slate-900">Quick actions</h3>
          <p className="body-text mt-1">Jump straight into your workspace.</p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;

            return (
              <Link
                key={action.title}
                to={action.path}
                className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-violet-200 hover:shadow-md"
              >
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 text-violet-600 transition group-hover:bg-violet-600 group-hover:text-white">
                  <Icon size={21} />
                </div>

                <h4 className="font-semibold text-slate-900">{action.title}</h4>

                <p className="mt-1 text-sm leading-relaxed text-slate-500">
                  {action.description}
                </p>

                <p className="mt-4 text-xs font-semibold text-violet-600">
                  Open workspace →
                </p>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <Sparkles size={21} />
          </div>

          <div>
            <h3 className="font-semibold text-slate-900">
              Your workspace is ready
            </h3>

            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-500">
              Your application shell, authentication, document library and AI
              document conversation workspace are being connected.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------
// Application Routes
// ---------------------------------------------

function AppRoutes() {
  return (
    <Routes>
      {/* Public authentication pages */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected application workspace */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />

          <Route path="library" element={<LibraryPage />} />

          <Route path="reader" element={<PDFReaderPage />} />

          <Route path="assistant" element={<AssistantPage />} />

          {/* Research */}
          <Route
            path="research"
            element={
              <PlaceholderPage
                title="Research"
                description="Explore documents and organize your research."
                icon={FlaskConical}
              />
            }
          />

          {/* Notebook */}
          <Route
            path="notebook"
            element={
              <PlaceholderPage
                title="Notebook"
                description="Create and organize your notes."
                icon={NotebookPen}
              />
            }
          />

          {/* Learning Studio */}
          <Route path="learning" element={<LearningPage />} />

          {/* Quiz Taking */}
          <Route path="learning/quizzes/:id" element={<QuizTakingPage />} />

          {/* Quiz Results */}
          <Route
            path="learning/quizzes/:id/results"
            element={<QuizResultsPage />}
          />

          {/* Audiobook */}
          <Route
            path="audiobook"
            element={
              <PlaceholderPage
                title="Audiobook"
                description="Listen to your documents with text-to-speech."
                icon={Headphones}
              />
            }
          />

          {/* Translation */}
          <Route
            path="translation"
            element={
              <PlaceholderPage
                title="Translation"
                description="Translate document content into other languages."
                icon={Languages}
              />
            }
          />

          {/* Analytics */}
          <Route
            path="analytics"
            element={
              <PlaceholderPage
                title="Analytics"
                description="Track your reading and learning activity."
                icon={ChartNoAxesCombined}
              />
            }
          />

          {/* Settings */}
          <Route
            path="settings"
            element={
              <PlaceholderPage
                title="Settings"
                description="Manage your account and workspace preferences."
                icon={Settings}
              />
            }
          />
        </Route>
      </Route>

      {/* Unknown routes */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// ---------------------------------------------
// Main Application
// ---------------------------------------------

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen flex-col">
        <main className="flex-1">
          <AppRoutes />
        </main>

        <Footer />
      </div>
    </BrowserRouter>
  );
}
