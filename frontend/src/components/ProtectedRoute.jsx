import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { authApi } from "../services/api";

export default function ProtectedRoute() {
  const location = useLocation();
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem("carebridge_token");

    if (!token) {
      setStatus("unauthenticated");
      return () => {
        active = false;
      };
    }

    authApi
      .me()
      .then(({ data }) => {
        if (!data.user) {
          throw new Error("Invalid user response");
        }

        if (!active) return;
        localStorage.setItem("carebridge_user", JSON.stringify(data.user));
        setStatus("authenticated");
      })
      .catch(() => {
        if (!active) return;
        localStorage.removeItem("carebridge_token");
        localStorage.removeItem("carebridge_user");
        setStatus("unauthenticated");
      });

    return () => {
      active = false;
    };
  }, []);

  if (status === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
        <div
          className="rounded-2xl border border-slate-800 bg-slate-900 px-6 py-5 text-center shadow-xl"
          role="status"
          aria-live="polite"
        >
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-cyan-400" />
          <p className="font-semibold">Verifying your session...</p>
          <p className="mt-1 text-sm text-slate-400">Please wait while we secure your account.</p>
        </div>
      </main>
    );
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
