export interface ToastMessage { id: number; text: string; kind: "success" | "error" }
export function Toasts({ messages }: { messages: ToastMessage[] }) {
  return <div className="fixed right-4 top-20 z-50 space-y-2">{messages.map((item) => <div key={item.id} role="status" className={`rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg ${item.kind === "success" ? "bg-brand" : "bg-red-600"}`}>{item.text}</div>)}</div>;
}
