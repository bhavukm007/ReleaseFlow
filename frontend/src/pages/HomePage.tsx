import { ArrowUpDown, Plus, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { releaseApi } from "../api/releases";
import { CreateReleaseModal } from "../components/CreateReleaseModal";
import { ReleaseCard } from "../components/ReleaseCard";
import { Toasts } from "../components/Toast";
import { useToast } from "../hooks/useToast";
import type { Release, ReleaseInput } from "../types";

export function HomePage() {
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [descending, setDescending] = useState(false);
  const [modal, setModal] = useState(false);
  const { messages, notify } = useToast();
  const load = () => { setLoading(true); setError(""); releaseApi.list().then(setReleases).catch(() => setError("We couldn’t load releases. Check that the API is running and try again.")).finally(() => setLoading(false)); };
  useEffect(load, []);
  const visible = useMemo(() => releases.filter((item) => item.name.toLowerCase().includes(query.toLowerCase())).sort((a, b) => (a.due_date.localeCompare(b.due_date)) * (descending ? -1 : 1)), [releases, query, descending]);
  const create = async (data: ReleaseInput) => {
    try { const item = await releaseApi.create({ ...data, additional_info: data.additional_info || null }); setReleases((items) => [...items, item]); setModal(false); notify("Release created"); }
    catch { notify("Couldn’t create release", "error"); }
  };
  return <><Toasts messages={messages} /><section className="bg-ink text-white"><div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16"><p className="mb-3 text-sm font-bold uppercase tracking-[.25em] text-emerald-300">Release operations</p><div className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div><h1 className="max-w-2xl text-4xl font-black tracking-tight sm:text-5xl">Every launch, clearly on track.</h1><p className="mt-4 max-w-xl text-lg text-slate-300">One calm place for the checks that turn “nearly ready” into shipped.</p></div><button className="btn-primary bg-coral hover:bg-orange-500" onClick={() => setModal(true)}><Plus size={20} />New release</button></div></div></section>
    <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6"><div className="mb-7 flex flex-col gap-4 sm:flex-row"><label className="relative flex-1"><span className="sr-only">Search releases</span><Search className="absolute left-4 top-3.5 text-slate-400" size={20} /><input value={query} onChange={(e) => setQuery(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-12 pr-4 outline-none focus:border-brand focus:ring-2 focus:ring-brand/10" placeholder="Search releases by name…" /></label><button onClick={() => setDescending((value) => !value)} className="btn-secondary"><ArrowUpDown size={18} />Due date: {descending ? "Latest" : "Soonest"}</button></div>
      {loading ? <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{[1,2,3].map((n) => <div key={n} className="h-56 animate-pulse rounded-2xl bg-white" />)}</div> : error ? <div className="state"><h2>Something went off course</h2><p>{error}</p><button className="btn-primary mt-4" onClick={load}>Try again</button></div> : visible.length ? <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{visible.map((release) => <ReleaseCard key={release.id} release={release} />)}</div> : <div className="state"><h2>{query ? "No matching releases" : "Your release runway is clear"}</h2><p>{query ? "Try another name or clear your search." : "Create your first release to start tracking its path to production."}</p>{!query && <button className="btn-primary mt-4" onClick={() => setModal(true)}><Plus size={18} />Create release</button>}</div>}
    </section>{modal && <CreateReleaseModal onClose={() => setModal(false)} onCreate={create} />}</>;
}
