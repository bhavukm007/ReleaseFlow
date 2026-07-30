import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

interface WorkspaceValue { teamId: string | null; setTeamId: (teamId: string | null) => void }
const WorkspaceContext = createContext<WorkspaceValue | null>(null);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [teamId, setTeamId] = useState<string | null>(null);
  const value = useMemo(() => ({ teamId, setTeamId }), [teamId]);
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}
export function useWorkspace() {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return value;
}
