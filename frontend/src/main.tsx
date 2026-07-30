import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { AuthProvider } from "./contexts/AuthContext";
import { WorkspaceProvider } from "./contexts/WorkspaceContext";
import { retryDelay, shouldRetryQuery } from "./api/retry";
import "./index.css";

const queryClient = new QueryClient({ defaultOptions: { queries: {
  staleTime: 30_000,
  retry: shouldRetryQuery,
  retryDelay,
  refetchOnWindowFocus: true,
} } });
ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><QueryClientProvider client={queryClient}><AuthProvider><WorkspaceProvider><App /></WorkspaceProvider></AuthProvider></QueryClientProvider></React.StrictMode>);
