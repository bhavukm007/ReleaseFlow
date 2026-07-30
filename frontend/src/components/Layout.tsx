import { useQuery } from "@tanstack/react-query";
import { Bell, LogOut, Moon, Rocket, Settings, Sun, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { teamApi } from "../api/teams";
import { useAuth } from "../contexts/AuthContext";
import { useWorkspace } from "../contexts/WorkspaceContext";

export function Layout() {
  const { user, logout } = useAuth(); const navigate = useNavigate();
  const { teamId, setTeamId } = useWorkspace();
  const { data: teams = [] } = useQuery({ queryKey: ["teams"], queryFn: teamApi.list });
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const invitations = teams.flatMap((team) => team.invitations.map((invitation) => ({ ...invitation, team: team.name })));
  const [dark, setDark] = useState(() => localStorage.getItem("releaseflow-theme") === "dark");
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); localStorage.setItem("releaseflow-theme", dark ? "dark" : "light"); }, [dark]);
  const signOut = async () => { await logout(); navigate("/login"); };
  return <div className="min-h-screen bg-cream text-ink dark:bg-slate-950 dark:text-slate-100">
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-2 text-xl font-black"><span className="rounded-lg bg-brand p-2 text-white"><Rocket size={20} /></span><span className="hidden sm:inline">ReleaseFlow</span></Link>
        <div className="flex items-center gap-1 sm:gap-2"><select aria-label="Workspace" value={teamId ?? ""} onChange={(event) => setTeamId(event.target.value || null)} className="max-w-32 rounded-lg border border-slate-200 bg-white px-2 py-2 text-sm font-semibold dark:border-slate-700 dark:bg-slate-800 sm:max-w-none sm:px-3"><option value="">My Releases</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select>
          <Link to="/teams" aria-label="Teams" className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"><Users size={19} /></Link><div className="relative"><button aria-label="Notifications" onClick={() => setNotificationsOpen((value) => !value)} className="relative rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"><Bell size={19} />{invitations.length > 0 && <span className="absolute right-0 top-0 grid h-4 min-w-4 place-items-center rounded-full bg-coral px-1 text-[10px] font-bold text-white">{invitations.length}</span>}</button>{notificationsOpen && <div className="absolute right-0 mt-2 w-72 rounded-xl border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-700 dark:bg-slate-800"><p className="px-2 pb-2 text-sm font-bold">Notifications</p>{invitations.length ? invitations.map((item) => <Link key={item.id} to="/teams" onClick={() => setNotificationsOpen(false)} className="block rounded-lg px-2 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700"><strong>{item.email}</strong> is invited to {item.team} as {item.role}.</Link>) : <p className="px-2 py-4 text-sm text-slate-500">You’re all caught up.</p>}</div>}</div><button aria-label="Toggle dark mode" onClick={() => setDark((value) => !value)} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800">{dark ? <Sun size={19} /> : <Moon size={19} />}</button>
          <div className="relative"><button aria-label="Profile menu" onClick={() => setProfileOpen((value) => !value)} className="grid h-9 w-9 place-items-center rounded-full bg-brand font-bold text-white">{user?.full_name.charAt(0).toUpperCase()}</button>{profileOpen && <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-700 dark:bg-slate-800"><div className="px-3 py-2"><p className="font-bold">{user?.full_name}</p><p className="truncate text-xs text-slate-500">{user?.email}</p></div><Link to="/settings" onClick={() => setProfileOpen(false)} className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700"><Settings size={16} />Settings</Link><button onClick={signOut} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50"><LogOut size={16} />Log out</button></div>}</div>
        </div>
      </div>
    </header>
    <main><Outlet /></main>
  </div>;
}
