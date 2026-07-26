export const STEP_NAMES = [
  "Code Freeze", "QA Completed", "Documentation Updated", "Security Review",
  "Performance Testing", "Deployment Ready", "Production Deployment", "Post Deployment Verification",
] as const;
export type Status = "planned" | "ongoing" | "done";
export interface Release {
  id: number; name: string; due_date: string; additional_info: string | null;
  steps: Record<string, boolean>; status: Status; completed_steps: number; total_steps: number;
  created_at: string; updated_at: string;
}
export interface ReleaseInput { name: string; due_date: string; additional_info?: string | null }
