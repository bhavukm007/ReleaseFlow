import { ArrowLeft, CalendarDays, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { releaseApi } from "../api/releases";
import { ProgressBar } from "../components/ProgressBar";
import { StatusBadge } from "../components/StatusBadge";
import { Toasts } from "../components/Toast";
import { useToast } from "../hooks/useToast";
import { STEP_NAMES, type Release } from "../types";

export function ReleaseDetailsPage() {
  const { id } = useParams(); const navigate = useNavigate(); const releaseId = Number(id);
  const [release, setRelease] = useState<Release | null>(null); const [info, setInfo] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [saving, setSaving] = useState(false); const [updatingSteps, setUpdatingSteps] = useState(false);
  const { messages, notify } = useToast();
  useEffect(() => { releaseApi.get(releaseId).then((item) => { setRelease(item); setInfo(item.additional_info ?? ""); }).catch(() => setError("This release could not be found or loaded.")).finally(() => setLoading(false)); }, [releaseId]);
  const toggle = async (name: string) => {
    if (!release || updatingSteps) return; const previous = release; const steps = { ...release.steps, [name]: !release.steps[name] }; const completed_steps = Object.values(steps).filter(Boolean).length; const optimistic: Release = { ...release, steps, completed_steps, status: completed_steps === 0 ? "planned" : completed_steps === release.total_steps ? "done" : "ongoing" }; setRelease(optimistic); setUpdatingSteps(true);
    try { setRelease(await releaseApi.updateSteps(release.id, steps)); notify("Checklist updated"); } catch { setRelease(previous); notify("Update failed — your change was restored", "error"); } finally { setUpdatingSteps(false); }
  };
  const saveInfo = async () => { if (!release) return; setSaving(true); try { setRelease(await releaseApi.updateInfo(release.id, info.trim() || null)); notify("Additional information saved"); } catch { notify("Couldn’t save information", "error"); } finally { setSaving(false); } };
  const remove = async () => { if (!release || !window.confirm(`Delete “${release.name}”? This cannot be undone.`)) return; try { await releaseApi.delete(release.id); navigate("/"); } catch { notify("Couldn’t delete release", "error"); } };
  if (loading) return <div className="mx-auto max-w-5xl p-6"><div className="h-96 animate-pulse rounded-2xl bg-white" /></div>;
  if (error || !release) return <div className="state mx-auto mt-16 max-w-xl"><h2>Release unavailable</h2><p>{error}</p><Link className="btn-primary mt-4" to="/">Back to releases</Link></div>;
  return <><Toasts messages={messages} /><div className="mx-auto max-w-5xl px-4 py-8 sm:px-6"><Link to="/" className="mb-7 inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-brand"><ArrowLeft size={18} />All releases</Link>
    <section className="rounded-2xl bg-ink p-6 text-white sm:p-8"><div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start"><div><StatusBadge status={release.status} /><h1 className="mt-4 text-3xl font-black sm:text-4xl">{release.name}</h1><p className="mt-3 flex items-center gap-2 text-slate-300"><CalendarDays size={18} />Due {new Date(`${release.due_date}T00:00:00`).toLocaleDateString(undefined, { dateStyle: "long" })}</p></div><button onClick={remove} className="inline-flex items-center gap-2 self-start rounded-lg px-3 py-2 text-sm font-semibold text-red-300 hover:bg-white/10"><Trash2 size={17} />Delete</button></div><div className="mt-8 [&_span]:text-slate-300"><ProgressBar completed={release.completed_steps} total={release.total_steps} /></div></section>
    <div className="mt-6 grid gap-6 lg:grid-cols-[1.25fr_.75fr]"><section className="panel"><p className="eyebrow">Release checklist</p><h2 className="section-title">Readiness steps</h2><div className="mt-5 divide-y divide-slate-100">{STEP_NAMES.map((name, index) => <label key={name} className={`flex items-center gap-4 py-4 ${updatingSteps ? "cursor-wait" : "cursor-pointer"}`}><input type="checkbox" checked={release.steps[name]} disabled={updatingSteps} onChange={() => toggle(name)} className="h-5 w-5 rounded border-slate-300 accent-brand" /><span className={`flex-1 font-semibold ${release.steps[name] ? "text-slate-400 line-through" : ""}`}>{name}</span><span className="text-xs font-bold text-slate-400">{String(index + 1).padStart(2, "0")}</span></label>)}</div></section>
      <section className="panel self-start"><p className="eyebrow">Notes & context</p><h2 className="section-title">Additional information</h2><textarea value={info} onChange={(e) => setInfo(e.target.value)} rows={10} className="mt-5 w-full resize-y rounded-xl border border-slate-200 p-4 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/10" placeholder="Add rollout notes, links, owners…" /><button disabled={saving || info === (release.additional_info ?? "")} onClick={saveInfo} className="btn-primary mt-4 w-full"><Save size={18} />{saving ? "Saving…" : "Save information"}</button></section></div>
  </div></>;
}
