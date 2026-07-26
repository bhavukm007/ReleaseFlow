import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { ReleaseDetailsPage } from "./pages/ReleaseDetailsPage";

const router = createBrowserRouter([{ element: <Layout />, children: [{ path: "/", element: <HomePage /> }, { path: "/releases/:id", element: <ReleaseDetailsPage /> }] }]);
export function App() { return <RouterProvider router={router} />; }
