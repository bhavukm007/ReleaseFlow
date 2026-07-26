import { useState } from "react";
import type { ToastMessage } from "../components/Toast";

export function useToast() {
  const [messages, setMessages] = useState<ToastMessage[]>([]);
  const notify = (text: string, kind: ToastMessage["kind"] = "success") => {
    const id = Date.now();
    setMessages((items) => [...items, { id, text, kind }]);
    window.setTimeout(() => setMessages((items) => items.filter((item) => item.id !== id)), 3000);
  };
  return { messages, notify };
}
