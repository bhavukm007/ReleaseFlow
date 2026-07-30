import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAccessToken, websocketUrl } from "../api/client";

export function useRealtime() {
  const queryClient = useQueryClient();
  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    const socket = new WebSocket(websocketUrl(token));
    socket.onmessage = () => {
      void queryClient.invalidateQueries({ queryKey: ["releases"] });
      void queryClient.invalidateQueries({ queryKey: ["release"] });
      void queryClient.invalidateQueries({ queryKey: ["activities"] });
      void queryClient.invalidateQueries({ queryKey: ["teams"] });
    };
    const keepAlive = window.setInterval(() => { if (socket.readyState === WebSocket.OPEN) socket.send("ping"); }, 25_000);
    return () => { window.clearInterval(keepAlive); socket.close(); };
  }, [queryClient]);
}
