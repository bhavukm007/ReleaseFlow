import type { Status } from "../types";

const styles: Record<Status, string> = {
  planned: "bg-slate-100 text-slate-600",
  ongoing: "bg-amber-100 text-amber-800 animate-pulse",
  done: "bg-emerald-100 text-emerald-800",
};
export function StatusBadge({ status }: { status: Status }) {
  return <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${styles[status]}`}>{status}</span>;
}
