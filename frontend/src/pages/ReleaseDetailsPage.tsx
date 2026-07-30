import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, GripVertical, Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { releaseApi } from "../api/releases";
import { teamApi } from "../api/teams";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { Toasts } from "../components/Toast";
import { useRealtime } from "../hooks/useRealtime";
import { useToast } from "../hooks/useToast";
import type { Release } from "../types";

const activityCopy: Record<string, string> = {
  release_created: "created the release", release_updated: "updated the release",
  checklist_completed: "completed", checklist_unchecked: "unchecked", step_deleted: "deleted step",
  notes_updated: "updated release notes",
};

export function ReleaseDetailsPage() {
  const { id } = useParams(); const navigate = useNavigate(); const releaseId = Number(id); const queryClient = useQueryClient(); useRealtime();
  const { messages, notify } = useToast(); const [info, setInfo] = useState(""); const [editing, setEditing] = useState(false); const [dragged, setDragged] = useState<number | null>(null);
  const releaseQuery = useQuery({ queryKey: ["release", releaseId], queryFn: () => releaseApi.get(releaseId), enabled: Number.isInteger(releaseId) });
  const activitiesQuery = useQuery({ queryKey: ["activities", releaseId], queryFn: () => releaseApi.activities(releaseId), enabled: !!releaseQuery.data });
  const teamsQuery = useQuery({ queryKey: ["teams"], queryFn: teamApi.list });
  const release = releaseQuery.data;
  useEffect(() => { if (release) setInfo(release.additional_info ?? ""); }, [release]);
  const canDelete = useMemo(() => !release?.team_id || ["owner", "admin"].includes(teamsQuery.data?.find((team) => team.id === release.team_id)?.role ?? ""), [release, teamsQuery.data]);
  const checklistMutation = useMutation({
    mutationFn: (steps: Record<string, boolean>) => releaseApi.updateChecklist(releaseId, steps),
    onMutate: async (steps) => {
      await queryClient.cancelQueries({ queryKey: ["release", releaseId] });
      const previous = queryClient.getQueryData<Release>(["release", releaseId]);
      if (previous) { const completed = Object.values(steps).filter(Boolean).length; queryClient.setQueryData<Release>(["release", releaseId], { ...previous, steps, completed_steps: completed, total_steps: Object.keys(steps).length, status: completed === 0 ? "planned" : completed === Object.keys(steps).length ? "done" : "ongoing" }); }
      return { previous };
    },
    onError: (_error, _steps, context) => { if (context?.previous) queryClient.setQueryData(["release", releaseId], context.previous); notify("Update failed — your change was restored", "error"); },
    onSuccess: (updated) => { queryClient.setQueryData(["release", releaseId], updated); void queryClient.invalidateQueries({ queryKey: ["activities", releaseId] }); },
  });
  const updateSteps = (steps: Record<string, boolean>) => checklistMutation.mutate(steps);
  const rename = (oldName: string, newName: string) => { if (!release || !newName.trim() || newName === oldName || (newName in release.steps)) return; const next: Record<string, boolean> = {}; Object.entries(release.steps).forEach(([name, done]) => { next[name === oldName ? newName.trim() : name] = done; }); updateSteps(next); };
  const removeStep = (name: string) => { if (!release || Object.keys(release.steps).length === 1) return; const next = { ...release.steps }; delete next[name]; updateSteps(next); };
  const addStep = () => { if (!release) return; let number = Object.keys(release.steps).length + 1; while (`New Step ${number}` in release.steps) number += 1; updateSteps({ ...release.steps, [`New Step ${number}`]: false }); };
  const drop = (target: number) => { if (!release || dragged === null || dragged === target) return; const entries = Object.entries(release.steps); const [entry] = entries.splice(dragged, 1); entries.splice(target, 0, entry); setDragged(null); updateSteps(Object.fromEntries(entries)); };
  const saveInfo = async () => { if (!release) return; try { const updated = await releaseApi.updateInfo(release.id, info.trim() || null); queryClient.setQueryData(["release", releaseId], updated); void queryClient.invalidateQueries({ queryKey: ["activities", releaseId] }); notify("Additional information saved"); } catch { notify("Couldn’t save information", "error"); } };
  const remove = async () => { if (!release || !window.confirm(`Delete “${release.name}”? This cannot be undone.`)) return; try { await releaseApi.delete(release.id); navigate("/"); } catch { notify("You do not have permission to delete this release", "error"); } };
  if (releaseQuery.isLoading) return <div className="mx-auto max-w-5xl p-6"><div className="h-96 animate-pulse rounded-2xl bg-white dark:bg-slate-900" /></div>;
  if (releaseQuery.isError || !release) return <div className="state mx-auto mt-16 max-w-xl"><h2>Release unavailable</h2><p>This release does not exist or you do not have access.</p><Link className="btn-primary mt-4" to="/">Back to releases</Link></div>;
  return <><Toasts messages={messages} /><div className="mx-auto max-w-6xl px-4 py-8 sm:px-6"><Link to="/" className="mb-7 inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-brand"><ArrowLeft size={18} />All releases</Link>
    <section className="rounded-2xl bg-ink p-6 text-white sm:p-8"><div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start"><div><StatusBadge status={release.status} /><h1 className="mt-4 text-3xl font-black sm:text-4xl">{release.name}</h1><p className="mt-3 flex items-center gap-2 text-slate-300"><CalendarDays size={18} />Due {new Date(`${release.due_date}T00:00:00`).toLocaleDateString(undefined, { dateStyle: "long" })}</p></div>{canDelete && <button onClick={remove} className="inline-flex items-center gap-2 self-start rounded-lg px-3 py-2 text-sm font-semibold text-red-300 hover:bg-white/10"><Trash2 size={17} />Delete</button>}</div><div className="mt-8 [&_span]:text-slate-300"><ProgressBar completed={release.completed_steps} total={release.total_steps} /></div></section>
    <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_.7fr_.8fr]"><section className="panel"><div className="flex items-center justify-between"><div><p className="eyebrow">Release checklist</p><h2 className="section-title">Readiness steps</h2></div><div className="flex gap-2"><button onClick={() => setEditing((value) => !value)} className="btn-secondary px-3 py-2 text-sm">{editing ? "Done" : "Edit"}</button>{editing && <button onClick={addStep} className="btn-primary px-3 py-2 text-sm"><Plus size={16} />Add</button>}</div></div><div className="mt-5 divide-y divide-slate-100 dark:divide-slate-800">{Object.entries(release.steps).map(([name, done], index) => <div key={name} draggable={editing} onDragStart={() => setDragged(index)} onDragOver={(event) => event.preventDefault()} onDrop={() => drop(index)} className="flex items-center gap-3 py-4">{editing && <GripVertical className="cursor-grab text-slate-400" size={18} />}<input type="checkbox" checked={done} disabled={checklistMutation.isPending || editing} onChange={() => updateSteps({ ...release.steps, [name]: !done })} aria-label={name} className="h-5 w-5 accent-brand" />{editing ? <input aria-label={`Rename ${name}`} defaultValue={name} onBlur={(event) => rename(name, event.target.value)} className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-transparent px-2 py-1 font-semibold" /> : <span className={`flex-1 font-semibold ${done ? "text-slate-400 line-through" : ""}`}>{name}</span>}{editing && <button aria-label={`Delete ${name}`} disabled={Object.keys(release.steps).length === 1} onClick={() => removeStep(name)} className="rounded p-1 text-red-500 hover:bg-red-50"><Trash2 size={16} /></button>}</div>)}</div></section>
      <section className="panel self-start"><p className="eyebrow">Notes & context</p><h2 className="section-title">Additional information</h2><textarea value={info} onChange={(event) => setInfo(event.target.value)} rows={10} className="mt-5 w-full resize-y rounded-xl border border-slate-200 bg-transparent p-4 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/10" placeholder="Add rollout notes, links, owners…" /><button disabled={info === (release.additional_info ?? "")} onClick={saveInfo} className="btn-primary mt-4 w-full"><Save size={18} />Save information</button></section>
      <section className="panel self-start"><p className="eyebrow">Audit log</p><h2 className="section-title">Activity</h2><div className="mt-5 max-h-[520px] space-y-5 overflow-y-auto">{activitiesQuery.isLoading ? [1,2,3].map((item) => <div key={item} className="h-14 animate-pulse rounded-lg bg-slate-100" />) : activitiesQuery.data?.length ? activitiesQuery.data.map((activity) => <article key={activity.id} className="border-l-2 border-brand/30 pl-4"><time className="text-xs text-slate-400">{new Date(activity.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</time><p className="mt-1 text-sm"><strong>{activity.user_name}</strong> {activityCopy[activity.action] ?? activity.action.replaceAll("_", " ")} {typeof activity.metadata.step === "string" && <q className="font-semibold">{activity.metadata.step}</q>}</p></article>) : <p className="text-sm text-slate-500">No activity yet.</p>}</div></section></div>
  </div></>;
}
