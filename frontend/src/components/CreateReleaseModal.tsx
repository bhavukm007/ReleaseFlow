import { zodResolver } from "@hookform/resolvers/zod";
import { GripVertical, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { STEP_NAMES, type ReleaseInput } from "../types";

const schema = z.object({ name: z.string().trim().min(1, "Name is required"), due_date: z.string().min(1, "Due date is required"), additional_info: z.string().optional() });

export function CreateReleaseModal({ onClose, onCreate, teamId = null }: { onClose: () => void; onCreate: (data: ReleaseInput) => Promise<void>; teamId?: string | null }) {
  const [steps, setSteps] = useState<string[]>([...STEP_NAMES]);
  const [dragged, setDragged] = useState<number | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<ReleaseInput>({ resolver: zodResolver(schema) });
  const submit = (data: ReleaseInput) => onCreate({ ...data, checklist_items: steps, team_id: teamId });
  const rename = (index: number, name: string) => setSteps((items) => items.map((item, position) => position === index ? name : item));
  const remove = (index: number) => setSteps((items) => items.filter((_, position) => position !== index));
  const drop = (target: number) => {
    if (dragged === null || dragged === target) return;
    setSteps((items) => { const next = [...items]; const [item] = next.splice(dragged, 1); next.splice(target, 0, item); return next; });
    setDragged(null);
  };
  return <div className="fixed inset-0 z-40 grid place-items-center overflow-y-auto bg-ink/50 p-4" role="dialog" aria-modal="true" aria-labelledby="create-title" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <form onSubmit={handleSubmit(submit)} className="my-4 w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
      <div className="mb-6 flex items-center justify-between"><div><p className="eyebrow">New milestone</p><h2 id="create-title" className="text-2xl font-black">Create release</h2></div><button type="button" onClick={onClose} aria-label="Close" className="rounded-lg p-2 hover:bg-slate-100"><X /></button></div>
      <label className="field">Release name<input autoFocus {...register("name")} placeholder="e.g. Summer Launch" />{errors.name && <span>{errors.name.message}</span>}</label>
      <label className="field">Due date<input type="date" {...register("due_date")} />{errors.due_date && <span>{errors.due_date.message}</span>}</label>
      <label className="field">Additional information <em>Optional</em><textarea rows={3} {...register("additional_info")} placeholder="Context, links, rollout notes…" /></label>
      <div className="mt-5"><div className="mb-3 flex items-center justify-between"><div><p className="font-bold">Checklist</p><p className="text-xs text-slate-500">Drag to reorder. Names must be unique.</p></div><button type="button" className="btn-secondary px-3 py-2 text-sm" onClick={() => setSteps((items) => [...items, `New Step ${items.length + 1}`])}><Plus size={16} />Add step</button></div>
        <div className="max-h-56 space-y-2 overflow-y-auto">{steps.map((step, index) => <div key={`${index}-${step}`} draggable onDragStart={() => setDragged(index)} onDragOver={(event) => event.preventDefault()} onDrop={() => drop(index)} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-800"><GripVertical className="cursor-grab text-slate-400" size={18} /><input aria-label={`Step ${index + 1}`} value={step} onChange={(event) => rename(index, event.target.value)} className="min-w-0 flex-1 bg-transparent px-2 py-1 text-sm font-semibold outline-none" /><button type="button" aria-label={`Delete ${step}`} disabled={steps.length === 1} onClick={() => remove(index)} className="rounded p-1 text-red-500 hover:bg-red-50"><Trash2 size={16} /></button></div>)}</div>
      </div>
      <div className="mt-7 flex justify-end gap-3"><button type="button" className="btn-secondary" onClick={onClose}>Cancel</button><button disabled={isSubmitting || steps.some((item) => !item.trim()) || new Set(steps.map((item) => item.trim().toLowerCase())).size !== steps.length} className="btn-primary">{isSubmitting ? "Creating…" : "Create release"}</button></div>
    </form>
  </div>;
}
