import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--workspace-bg)]">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((current) => !current)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div
        className={[
          "min-h-screen transition-[margin] duration-200 ease-in-out",
          sidebarCollapsed ? "lg:ml-[82px]" : "lg:ml-[260px]",
        ].join(" ")}
      >
        <Topbar onOpenMobile={() => setMobileOpen(true)} />

        <main className="min-h-[calc(100vh-72px)]">
          <div className="page-container">
            <Outlet />
          </div>
        </main>

        <footer className="border-t border-slate-200 bg-white px-6 py-4 text-center text-xs text-slate-400">
          © {new Date().getFullYear()} FLIPBOOK-AI. Your intelligent reading
          workspace.
        </footer>
      </div>
    </div>
  );
}
