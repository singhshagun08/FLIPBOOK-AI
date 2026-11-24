import { useState } from "react";
import { Sparkles, BookOpen, ClipboardList, Layers } from "lucide-react";

import QuizGeneratorForm from "../components/QuizGeneratorForm";
import MyQuizzes from "../components/MyQuizzes";
import Flashcards from "../components/Flashcards";

type LearningTab = "generate" | "quizzes" | "flashcards";

const LearningPage = () => {
  const [activeTab, setActiveTab] = useState<LearningTab>("generate");

  const tabs = [
    {
      id: "generate" as const,
      label: "Generate Quiz",
      icon: Sparkles,
    },
    {
      id: "quizzes" as const,
      label: "My Quizzes",
      icon: ClipboardList,
    },
    {
      id: "flashcards" as const,
      label: "Flashcards",
      icon: Layers,
    },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-6">
      {/* PAGE HEADER */}

      <div className="rounded-2xl bg-gradient-to-r from-violet-700 to-indigo-600 p-6 text-white md:p-8">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-white/15 p-3">
            <BookOpen className="h-7 w-7" />
          </div>

          <div>
            <p className="text-sm text-violet-100">
              FLIPBOOK-AI Learning Studio
            </p>

            <h1 className="text-2xl font-bold md:text-3xl">
              Learn Smarter with AI
            </h1>
          </div>
        </div>

        <p className="mt-4 max-w-2xl text-sm leading-6 text-violet-100">
          Turn your uploaded PDFs into interactive quizzes and personalized
          learning experiences. Learn, practice, and track your progress.
        </p>
      </div>

      {/* NAVIGATION TABS */}

      <div className="flex gap-2 overflow-x-auto border-b border-slate-200 pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              aria-current={isActive ? "page" : undefined}
              className={`flex shrink-0 items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium transition ${
                isActive
                  ? "bg-violet-100 text-violet-700"
                  : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT */}

      <div>
        {/* GENERATE QUIZ */}

        {activeTab === "generate" && <QuizGeneratorForm />}

        {/* MY QUIZZES */}

        {activeTab === "quizzes" && <MyQuizzes />}

        {/* FLASHCARDS */}

        {activeTab === "flashcards" && <Flashcards />}
      </div>
    </div>
  );
};

export default LearningPage;
