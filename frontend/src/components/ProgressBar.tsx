export function ProgressBar({ completed, total }: { completed: number; total: number }) {
  const percent = total ? Math.round((completed / total) * 100) : 0;
  return (
    <div>
      <div className="mb-2 flex justify-between text-sm text-slate-600"><span>{completed} / {total} Completed</span><span>{percent}%</span></div>
      <div className="h-2.5 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-brand transition-all duration-500" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
