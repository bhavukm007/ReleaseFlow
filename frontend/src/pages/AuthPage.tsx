import { zodResolver } from "@hookform/resolvers/zod";
import { Rocket } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { useAuth } from "../contexts/AuthContext";

const loginSchema = z.object({ email: z.string().email(), password: z.string().min(1, "Password is required") });
const signupSchema = loginSchema.extend({ full_name: z.string().trim().min(2, "Full name is required"), password: z.string().min(10, "Use at least 10 characters") });
type AuthFields = { full_name?: string; email: string; password: string };

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { user, login, signup } = useAuth();
  const navigate = useNavigate(); const location = useLocation();
  const [serverError, setServerError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<AuthFields>({ resolver: zodResolver(mode === "login" ? loginSchema : signupSchema) });
  if (user) return <Navigate to="/" replace />;
  const submit = async (values: AuthFields) => {
    setServerError("");
    try {
      if (mode === "login") await login(values.email, values.password);
      else await signup(values.full_name!, values.email, values.password);
      navigate((location.state as { from?: { pathname?: string } })?.from?.pathname ?? "/", { replace: true });
    } catch (error: unknown) {
      setServerError((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Authentication failed. Please try again.");
    }
  };
  return <main className="grid min-h-screen bg-cream lg:grid-cols-2">
    <section className="hidden bg-ink p-12 text-white lg:flex lg:flex-col lg:justify-between"><Link to="/" className="flex items-center gap-2 text-xl font-black"><span className="rounded-lg bg-brand p-2"><Rocket size={20} /></span>ReleaseFlow</Link><div><p className="eyebrow text-emerald-300">Collaborative release operations</p><h1 className="mt-4 max-w-xl text-5xl font-black leading-tight">Ship together without losing the thread.</h1><p className="mt-5 max-w-lg text-lg text-slate-300">One secure workspace for owners, teams, dynamic checklists, and every decision between planning and production.</p></div><p className="text-sm text-slate-400">Secure by default · Real-time by design</p></section>
    <section className="grid place-items-center p-5"><form onSubmit={handleSubmit(submit)} className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm sm:p-9"><div className="mb-8 lg:hidden"><span className="text-xl font-black">ReleaseFlow</span></div><p className="eyebrow">{mode === "login" ? "Welcome back" : "Create your workspace"}</p><h2 className="section-title">{mode === "login" ? "Sign in" : "Create account"}</h2><p className="mt-2 text-sm text-slate-500">{mode === "login" ? "Continue to your releases and teams." : "Start shipping confidently with your team."}</p>
      {serverError && <div role="alert" className="mt-5 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-700">{serverError}</div>}
      <div className="mt-7">{mode === "signup" && <label className="field">Full name<input autoComplete="name" {...register("full_name")} />{errors.full_name && <span>{errors.full_name.message}</span>}</label>}<label className="field">Email<input type="email" autoComplete="email" {...register("email")} />{errors.email && <span>{errors.email.message}</span>}</label><label className="field">Password<input type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} {...register("password")} />{errors.password && <span>{errors.password.message}</span>}</label></div>
      {mode === "login" && <button type="button" className="mb-5 text-sm font-semibold text-brand" onClick={() => setServerError("Password reset is coming soon. Contact your workspace owner for help.")}>Forgot password?</button>}
      <button className="btn-primary w-full" disabled={isSubmitting}>{isSubmitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
      <p className="mt-6 text-center text-sm text-slate-500">{mode === "login" ? "New to ReleaseFlow?" : "Already have an account?"} <Link className="font-bold text-brand" to={mode === "login" ? "/signup" : "/login"}>{mode === "login" ? "Create account" : "Sign in"}</Link></p>
    </form></section>
  </main>;
}
