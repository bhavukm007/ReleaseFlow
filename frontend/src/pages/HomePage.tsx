import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUpDown, Clock3, Plus, Search } from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { releaseApi } from "../api/releases";
import { CreateReleaseModal } from "../components/CreateReleaseModal";
import { ReleaseCard } from "../components/ReleaseCard";
import { Toasts } from "../components/Toast";
import { useWorkspace } from "../contexts/WorkspaceContext";
import { useRealtime } from "../hooks/useRealtime";
import { useToast } from "../hooks/useToast";
import type { ReleaseInput } from "../types";

export function HomePage() {
  const { teamId } = useWorkspace(); const queryClient = useQueryClient(); useRealtime();
  const [query, setQuery] = useState(""); const deferredQuery = useDeferredValue(query);
  const [descending, setDescending] = useState(false); const [modal, setModal] = useState(false);
  const { messages, notify } = useToast();
  const releasesQuery = useQuery({ queryKey: ["releases", teamId], queryFn: () => releaseApi.list(teamId) });
  const activityQuery = useQuery({ queryKey: ["activities", "recent"], queryFn: releaseApi.recentActivities });
  useEffect(() => {
    const openCreate = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (event.key.toLowerCase() === "n" && !event.metaKey && !event.ctrlKey && !target?.matches("input, textarea, select")) {
        event.preventDefault();
        setModal(true);
      }
    };
    window.addEventListener("keydown", openCreate);
    return () => window.removeEventListener("keydown", openCreate);
  }, []);
  const createMutation = useMutation({
    mutationFn: releaseApi.create,
    onSuccess: (item) => { queryClient.setQueryData(["releases", teamId], (items: unknown) => [...((items as typeof releasesQuery.data) ?? []), item]); setModal(false); notify("Release created"); },
    onError: () => notify("Couldn’t create release", "error"),
  });
  const visible = useMemo(() => (releasesQuery.data ?? []).filter((item) => item.name.toLowerCase().includes(deferredQuery.toLowerCase())).sort((a, b) => a.due_date.localeCompare(b.due_date) * (descending ? -1 : 1)), [releasesQuery.data, deferredQuery, descending]);
  const create = async (data: ReleaseInput) => { await createMutation.mutateAsync({ ...data, additional_info: data.additional_info || null }); };
  return <><Toasts messages={messages} /><section className="bg-ink text-white"><div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14"><p className="mb-3 text-sm font-bold uppercase tracking-[.25em] text-emerald-300">{teamId ? "Team releases" : "My releases"}</p><div className="flex flex-col justify-between gap-6 md:flex-row md:items-end"><div><h1 className="max-w-2xl text-4xl font-black tracking-tight sm:text-5xl">Every launch, clearly on track.</h1><p className="mt-4 max-w-xl text-lg text-slate-300">One calm place for the checks that turn “nearly ready” into shipped.</p></div><button className="btn-primary bg-coral hover:bg-orange-500" onClick={() => setModal(true)}><Plus size={20} />New release</button></div></div></section>
    <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6"><div className="mb-7 flex flex-col gap-4 sm:flex-row"><label className="relative flex-1"><span className="sr-only">Search releases</span><Search className="absolute left-4 top-3.5 text-slate-400" size={20} /><input value={query} onChange={(event) => setQuery(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-12 pr-4 outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 dark:border-slate-700 dark:bg-slate-900" placeholder="Search releases by name…" /></label><button onClick={() => setDescending((value) => !value)} className="btn-secondary"><ArrowUpDown size={18} />Due date: {descending ? "Latest" : "Soonest"}</button></div>
      {releasesQuery.isLoading ? <div><div className="mb-5 text-center">{releasesQuery.failureCount > 0 && <><p className="font-bold text-ink dark:text-white">Starting server...</p><p className="mt-1 text-sm text-slate-500">ReleaseFlow is reconnecting automatically.</p></>}</div><div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{[1,2,3].map((number) => <div key={number} className="h-56 animate-pulse rounded-2xl bg-white dark:bg-slate-900" />)}</div></div> : releasesQuery.isError ? <div className="state"><h2>Something went off course</h2><p>We couldn’t load this workspace after several automatic attempts. Check your connection and try again.</p><button className="btn-primary mt-4" onClick={() => releasesQuery.refetch()}>Try again</button></div> : visible.length ? <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{visible.map((release) => <ReleaseCard key={release.id} release={release} />)}</div> : <div className="state"><h2>{query ? "No matching releases" : "Your release runway is clear"}</h2><p>{query ? "Try another name or clear your search." : "Create your first release to start tracking its path to production."}</p>{!query && <button className="btn-primary mt-4" onClick={() => setModal(true)}><Plus size={18} />Create release</button>}</div>}
      {activityQuery.data && activityQuery.data.length > 0 && <section className="mt-10 border-t border-slate-200 pt-7 dark:border-slate-800"><div className="mb-4 flex items-center gap-2"><Clock3 size={18} className="text-brand" /><h2 className="text-lg font-black">Recent activity</h2></div><div className="grid gap-3 md:grid-cols-2">{activityQuery.data.map((activity) => <article key={activity.id} className="rounded-xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900"><p><strong>{activity.user_name}</strong> {activity.action.replaceAll("_", " ")}</p><time className="mt-1 block text-xs text-slate-400">{new Date(activity.created_at).toLocaleString()}</time></article>)}</div></section>}
    </section>{modal && <CreateReleaseModal teamId={teamId} onClose={() => setModal(false)} onCreate={create} />}</>;
}
