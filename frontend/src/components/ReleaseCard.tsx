import { CalendarDays, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { Release } from "../types";
import { ProgressBar } from "./ProgressBar";
import { StatusBadge } from "./StatusBadge";

export function ReleaseCard({ release }: { release: Release }) {
  const date = new Date(`${release.due_date}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  return <Link to={`/releases/${release.id}`} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-brand/30 hover:shadow-lg">
    <div className="mb-6 flex items-start justify-between gap-3"><div><h3 className="text-lg font-bold">{release.name}</h3><p className="mt-2 flex items-center gap-2 text-sm text-slate-500"><CalendarDays size={16} />Due {date}</p></div><StatusBadge status={release.status} /></div>
    <ProgressBar completed={release.completed_steps} total={release.total_steps} />
    <div className="mt-5 flex items-center justify-end text-sm font-semibold text-brand">View release <ChevronRight className="transition group-hover:translate-x-1" size={18} /></div>
  </Link>;
}
