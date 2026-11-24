import { useState } from "react";
import { useLocation } from "react-router-dom";
import {
  Search,
  Bell,
  Menu,
  ChevronDown,
  UserRound,
  Settings,
  LogOut,
  HelpCircle,
} from "lucide-react";

type TopbarProps = {
  onOpenMobile: () => void;
};

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/library": "My Library",
  "/reader": "Reader",
  "/assistant": "AI Assistant",
  "/research": "Research",
  "/notebook": "Notebook",
  "/learning": "Learning",
  "/audiobook": "Audiobook",
  "/translation": "Translation",
  "/analytics": "Analytics",
  "/settings": "Settings",
};

export default function Topbar({ onOpenMobile }: TopbarProps) {
  const location = useLocation();
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const currentTitle = pageTitles[location.pathname] ?? "FLIPBOOK-AI";

  return (
    <header className="sticky top-0 z-30 flex h-[72px] items-center justify-between gap-4 border-b border-slate-200 bg-white/90 px-4 backdrop-blur-md sm:px-6 lg:px-8">
      {/* Left section */}
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobile}
          aria-label="Open navigation"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 lg:hidden"
        >
          <Menu size={21} />
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-base font-bold text-slate-900 sm:text-lg">
            {currentTitle}
          </h1>
          <p className="hidden text-xs text-slate-500 sm:block">
            Welcome to your reading workspace
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="hidden w-full max-w-md flex-1 md:block">
        <div className="relative">
          <Search
            size={17}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="search"
            placeholder="Search documents, notes, tools..."
            aria-label="Search workspace"
            className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-violet-400 focus:bg-white focus:ring-4 focus:ring-violet-500/10"
          />
          <span className="absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] text-slate-400 xl:block">
            Ctrl K
          </span>
        </div>
      </div>

      {/* Right section */}
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        {/* Notifications */}
        <div className="relative">
          <button
            type="button"
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
            onClick={() => {
              setNotificationsOpen((open) => !open);
              setProfileOpen(false);
            }}
            className="relative flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
          >
            <Bell size={19} />
            <span className="absolute right-2 top-2 h-2 w-2 rounded-full border-2 border-white bg-violet-500" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 top-12 z-50 w-72 rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">
                  Notifications
                </p>
                <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-semibold text-violet-600">
                  New
                </span>
              </div>
              <p className="text-xs leading-relaxed text-slate-500">
                You’re all caught up. Updates from your workspace will appear
                here.
              </p>
            </div>
          )}
        </div>

        <div className="hidden h-8 w-px bg-slate-200 sm:block" />

        {/* Profile */}
        <div className="relative">
          <button
            type="button"
            aria-expanded={profileOpen}
            onClick={() => {
              setProfileOpen((open) => !open);
              setNotificationsOpen(false);
            }}
            className="flex items-center gap-2 rounded-xl p-1.5 transition hover:bg-slate-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-xs font-bold text-violet-700">
              U
            </div>

            <div className="hidden text-left sm:block">
              <p className="text-xs font-semibold text-slate-800">User</p>
              <p className="text-[10px] text-slate-500">Personal account</p>
            </div>

            <ChevronDown size={15} className="hidden text-slate-400 sm:block" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 top-12 z-50 w-52 overflow-hidden rounded-xl border border-slate-200 bg-white py-2 shadow-xl">
              <div className="border-b border-slate-100 px-4 py-2">
                <p className="text-sm font-semibold text-slate-900">
                  Your Account
                </p>
                <p className="text-xs text-slate-500">Manage your workspace</p>
              </div>

              <button
                type="button"
                onClick={() => setProfileOpen(false)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-xs text-slate-600 hover:bg-slate-50"
              >
                <UserRound size={15} />
                Profile
              </button>

              <button
                type="button"
                onClick={() => setProfileOpen(false)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-xs text-slate-600 hover:bg-slate-50"
              >
                <Settings size={15} />
                Account settings
              </button>

              <button
                type="button"
                onClick={() => setProfileOpen(false)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-xs text-slate-600 hover:bg-slate-50"
              >
                <HelpCircle size={15} />
                Help and support
              </button>

              <div className="my-1 border-t border-slate-100" />

              <button
                type="button"
                onClick={() => setProfileOpen(false)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-xs text-red-600 hover:bg-red-50"
              >
                <LogOut size={15} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
