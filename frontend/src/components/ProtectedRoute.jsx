import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { authApi } from "../services/api";

export default function ProtectedRoute() {
  const location = useLocation();
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    const token = localStorage.getItem("carebridge_token");

    if (!token) {
      setStatus("unauthenticated");
      return;
    }

    authApi.me()
      .then(({ data }) => {
        if (!data.user) {
          throw new Error("Invalid user response");
        }

        localStorage.setItem("carebridge_user", JSON.stringify(data.user));
        setStatus("authenticated");
      })
      .catch(() => {
        localStorage.removeItem("carebridge_token");
        localStorage.removeItem("carebridge_user");
        setStatus("unauthenticated");
      });
  }, []);

  if (status === "checking") {
    return <div>Verifying your session...</div>;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
