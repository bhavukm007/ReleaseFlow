import { Rocket } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

export function Layout() {
  return <div className="min-h-screen bg-cream text-ink">
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 text-xl font-black"><span className="rounded-lg bg-brand p-2 text-white"><Rocket size={20} /></span>ReleaseFlow</Link>
        <span className="hidden text-sm text-slate-500 sm:block">Ship with confidence.</span>
      </div>
    </header>
    <main><Outlet /></main>
  </div>;
}
