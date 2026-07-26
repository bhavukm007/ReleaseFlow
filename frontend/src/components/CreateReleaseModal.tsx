import { zodResolver } from "@hookform/resolvers/zod";
import { X } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { ReleaseInput } from "../types";

const schema = z.object({ name: z.string().trim().min(1, "Name is required"), due_date: z.string().min(1, "Due date is required"), additional_info: z.string().optional() });

export function CreateReleaseModal({ onClose, onCreate }: { onClose: () => void; onCreate: (data: ReleaseInput) => Promise<void> }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<ReleaseInput>({ resolver: zodResolver(schema) });
  return <div className="fixed inset-0 z-40 grid place-items-center bg-ink/50 p-4" role="dialog" aria-modal="true" aria-labelledby="create-title" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <form onSubmit={handleSubmit(onCreate)} className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div className="mb-6 flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-brand">New milestone</p><h2 id="create-title" className="text-2xl font-black">Create release</h2></div><button type="button" onClick={onClose} aria-label="Close" className="rounded-lg p-2 hover:bg-slate-100"><X /></button></div>
      <label className="field">Release name<input autoFocus {...register("name")} placeholder="e.g. Summer Launch" />{errors.name && <span>{errors.name.message}</span>}</label>
      <label className="field">Due date<input type="date" {...register("due_date")} />{errors.due_date && <span>{errors.due_date.message}</span>}</label>
      <label className="field">Additional information <em>Optional</em><textarea rows={4} {...register("additional_info")} placeholder="Context, links, rollout notes…" /></label>
      <div className="mt-7 flex justify-end gap-3"><button type="button" className="btn-secondary" onClick={onClose}>Cancel</button><button disabled={isSubmitting} className="btn-primary">{isSubmitting ? "Creating…" : "Create release"}</button></div>
    </form>
  </div>;
}
