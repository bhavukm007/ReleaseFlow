import { useAuth } from "../contexts/AuthContext";

export function SettingsPage() {
  const { user } = useAuth();
  return <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6"><p className="eyebrow">Account</p><h1 className="section-title">Settings</h1><section className="panel mt-6"><div className="flex items-center gap-4"><div className="grid h-14 w-14 place-items-center rounded-full bg-brand text-xl font-black text-white">{user?.full_name.charAt(0).toUpperCase()}</div><div><h2 className="font-bold">{user?.full_name}</h2><p className="text-sm text-slate-500">{user?.email}</p></div></div><p className="mt-6 text-sm text-slate-500">Profile editing and password recovery are planned for a future release. Authentication and workspace access are active.</p></section></div>;
}
