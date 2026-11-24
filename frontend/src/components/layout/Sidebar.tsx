import { NavLink } from "react-router-dom";
import {
  BookOpen,
  LayoutDashboard,
  Library,
  BookMarked,
  MessageSquareText,
  FlaskConical,
  NotebookPen,
  GraduationCap,
  Headphones,
  Languages,
  ChartNoAxesCombined,
  Settings,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
} from "lucide-react";

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
};

const navigationGroups = [
  {
    label: "WORKSPACE",
    items: [
      { label: "Dashboard", path: "/", icon: LayoutDashboard },
      { label: "My Library", path: "/library", icon: Library },
      { label: "Reader", path: "/reader", icon: BookOpen },
    ],
  },
  {
    label: "AI TOOLS",
    items: [
      { label: "AI Assistant", path: "/assistant", icon: MessageSquareText },
      { label: "Research", path: "/research", icon: FlaskConical },
      { label: "Notebook", path: "/notebook", icon: NotebookPen },
    ],
  },
  {
    label: "LEARNING",
    items: [
      { label: "Learning", path: "/learning", icon: GraduationCap },
      { label: "Audiobook", path: "/audiobook", icon: Headphones },
      { label: "Translation", path: "/translation", icon: Languages },
    ],
  },
  {
    label: "MANAGEMENT",
    items: [
      {
        label: "Analytics",
        path: "/analytics",
        icon: ChartNoAxesCombined,
      },
      { label: "Settings", path: "/settings", icon: Settings },
    ],
  },
];

export default function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onCloseMobile,
}: SidebarProps) {
  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-950/50 lg:hidden"
        />
      )}

      <aside
        className={[
          "sidebar fixed inset-y-0 left-0 z-50 flex flex-col",
          "transition-all duration-200 ease-in-out",
          collapsed ? "w-[82px]" : "w-[260px]",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "lg:translate-x-0",
        ].join(" ")}
        style={{
          width: collapsed ? "82px" : "260px",
        }}
      >
        {/* Brand */}
        <div className="flex h-[72px] shrink-0 items-center justify-between border-b border-[var(--sidebar-border)] px-5">
          <NavLink
            to="/"
            onClick={onCloseMobile}
            className="flex min-w-0 items-center gap-3"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-lg shadow-violet-950/30">
              <BookMarked size={20} strokeWidth={2.2} />
            </div>

            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-[15px] font-bold tracking-tight text-white">
                  FLIPBOOK<span className="text-violet-400">.AI</span>
                </p>
                <p className="text-[10px] font-medium tracking-[0.16em] text-slate-400">
                  READ. LEARN. DISCOVER.
                </p>
              </div>
            )}
          </NavLink>

          <button
            type="button"
            onClick={onToggle}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-white lg:flex"
          >
            {collapsed ? (
              <PanelLeftOpen size={17} />
            ) : (
              <PanelLeftClose size={17} />
            )}
          </button>

          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close sidebar"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
          >
            <ChevronLeft size={19} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-7 overflow-y-auto px-3 py-6">
          {navigationGroups.map((group) => (
            <div key={group.label}>
              {!collapsed && (
                <p className="mb-3 px-3 text-[10px] font-bold tracking-[0.16em] text-slate-500">
                  {group.label}
                </p>
              )}

              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;

                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === "/"}
                      onClick={onCloseMobile}
                      title={collapsed ? item.label : undefined}
                      className={({ isActive }) =>
                        [
                          "sidebar-link group",
                          collapsed ? "justify-center px-0" : "",
                          isActive ? "active" : "",
                        ].join(" ")
                      }
                    >
                      <Icon size={19} strokeWidth={1.9} className="shrink-0" />

                      {!collapsed && (
                        <span className="truncate">{item.label}</span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* AI promotional panel */}
        {!collapsed && (
          <div className="mx-3 mb-4 rounded-xl border border-violet-400/20 bg-gradient-to-br from-violet-500/15 to-indigo-500/10 p-4">
            <div className="mb-2 flex items-center gap-2 text-violet-300">
              <Sparkles size={16} />
              <span className="text-xs font-semibold">AI Workspace</span>
            </div>

            <p className="mb-3 text-xs leading-relaxed text-slate-300">
              Turn your documents into an interactive learning experience.
            </p>

            <NavLink
              to="/assistant"
              onClick={onCloseMobile}
              className="flex items-center justify-center gap-2 rounded-lg bg-violet-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-violet-500"
            >
              Explore AI Tools
              <ChevronRight size={14} />
            </NavLink>
          </div>
        )}

        {/* Footer */}
        <div className="border-t border-[var(--sidebar-border)] p-4">
          <div
            className={[
              "flex items-center gap-3",
              collapsed ? "justify-center" : "",
            ].join(" ")}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-500/20 text-xs font-bold text-violet-200">
              U
            </div>

            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-white">
                  Your Workspace
                </p>
                <p className="text-[11px] text-slate-400">Personal account</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
