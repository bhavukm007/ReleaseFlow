import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";

const AuthPage = lazy(() => import("./pages/AuthPage").then((module) => ({ default: module.AuthPage })));
const HomePage = lazy(() => import("./pages/HomePage").then((module) => ({ default: module.HomePage })));
const ReleaseDetailsPage = lazy(() => import("./pages/ReleaseDetailsPage").then((module) => ({ default: module.ReleaseDetailsPage })));
const SettingsPage = lazy(() => import("./pages/SettingsPage").then((module) => ({ default: module.SettingsPage })));
const TeamsPage = lazy(() => import("./pages/TeamsPage").then((module) => ({ default: module.TeamsPage })));

const page = (element: ReactNode) => (
  <Suspense fallback={<div className="grid min-h-[60vh] place-items-center"><div className="h-10 w-10 animate-spin rounded-full border-4 border-brand border-t-transparent" /></div>}>
    {element}
  </Suspense>
);

const router = createBrowserRouter([
  { path: "/login", element: page(<AuthPage mode="login" />) },
  { path: "/signup", element: page(<AuthPage mode="signup" />) },
  { element: <ProtectedRoute />, children: [{ element: <Layout />, children: [
    { path: "/", element: page(<HomePage />) },
    { path: "/releases/:id", element: page(<ReleaseDetailsPage />) },
    { path: "/teams", element: page(<TeamsPage />) },
    { path: "/settings", element: page(<SettingsPage />) },
  ] }] },
]);
export function App() { return <RouterProvider router={router} />; }
