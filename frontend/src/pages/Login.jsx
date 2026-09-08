import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../services/api";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.login(form);
      localStorage.setItem("carebridge_token", data.access_token);
      localStorage.setItem("carebridge_user", JSON.stringify(data.user));
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.message || "Unable to sign in. Check your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-md">
        <Link to="/" className="text-sm font-semibold text-cyan-400">CareBridge AI</Link>
        <div className="mt-10 rounded-3xl bg-white p-8 text-slate-900 shadow-2xl">
          <h1 className="text-3xl font-bold">Welcome back</h1>
          <p className="mt-2 text-slate-500">Sign in to your CareBridge account.</p>
          {error && <p className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <form onSubmit={submit} className="mt-7 space-y-5">
            <label className="block text-sm font-medium">Email<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cyan-500" /></label>
            <label className="block text-sm font-medium">Password<input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cyan-500" /></label>
            <button disabled={loading} className="w-full rounded-xl bg-slate-950 px-4 py-3 font-semibold text-white disabled:opacity-60">{loading ? "Signing in..." : "Sign in"}</button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">New to CareBridge? <Link className="font-semibold text-cyan-600" to="/register">Create an account</Link></p>
        </div>
      </div>
    </main>
  );
}
