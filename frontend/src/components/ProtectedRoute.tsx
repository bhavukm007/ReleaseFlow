import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function ProtectedRoute() {
  const { user, loading, startingServer, startupError } = useAuth();
  const location = useLocation();
  if (loading) return <div className="min-h-screen bg-cream p-5 sm:p-8"><div className="mx-auto max-w-6xl"><div className="mb-10 h-14 animate-pulse rounded-xl bg-white" /><div className="mb-6 text-center"><div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand border-t-transparent" /><p className="mt-4 font-bold text-ink">{startingServer ? "Starting server..." : "Loading ReleaseFlow..."}</p>{startingServer && <p className="mt-1 text-sm text-slate-500">The free server is waking up. This can take about a minute.</p>}</div><div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="h-56 animate-pulse rounded-2xl bg-white" />)}</div></div></div>;
  if (startupError) return <div className="grid min-h-screen place-items-center bg-cream p-5"><div className="state max-w-lg"><h1>Server unavailable</h1><p>ReleaseFlow could not reach the API after several automatic attempts. Please try again in a moment.</p></div></div>;
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location }} />;
}
