export const STEP_NAMES = [
  "Code Freeze", "QA Completed", "Documentation Updated", "Security Review",
  "Performance Testing", "Deployment Ready", "Production Deployment", "Post Deployment Verification",
] as const;
export type Status = "planned" | "ongoing" | "done";
export interface Release {
  id: number; name: string; due_date: string; additional_info: string | null;
  steps: Record<string, boolean>; status: Status; completed_steps: number; total_steps: number;
  created_at: string; updated_at: string;
  owner_id: string; team_id: string | null;
}
export interface ReleaseInput { name: string; due_date: string; additional_info?: string | null; checklist_items?: string[]; team_id?: string | null }
export interface User { id: string; full_name: string; email: string; created_at: string; last_login: string | null }
export type TeamRole = "owner" | "admin" | "member";
export interface TeamMember { user_id: string; full_name: string; email: string; role: TeamRole }
export interface TeamInvitation { id: string; email: string; role: TeamRole; created_at: string }
export interface Team { id: string; name: string; owner_id: string; role: TeamRole; created_at: string; members: TeamMember[]; invitations: TeamInvitation[] }
export interface Activity { id: string; release_id: number | null; team_id: string | null; user_id: string; user_name: string; action: string; metadata: Record<string, unknown>; created_at: string }
