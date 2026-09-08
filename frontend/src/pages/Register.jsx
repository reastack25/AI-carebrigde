import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../services/api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "patient" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.register(form);
      localStorage.setItem("carebridge_token", data.access_token);
      localStorage.setItem("carebridge_user", JSON.stringify(data.user));
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.message || "Unable to create your account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-md">
        <Link to="/" className="text-sm font-semibold text-cyan-400">CareBridge AI</Link>
        <div className="mt-10 rounded-3xl bg-white p-8 text-slate-900 shadow-2xl">
          <h1 className="text-3xl font-bold">Create your account</h1>
          <p className="mt-2 text-slate-500">Start your CareBridge journey.</p>
          {error && <p className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <form onSubmit={submit} className="mt-7 space-y-5">
            <label className="block text-sm font-medium">Full name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cyan-500" /></label>
            <label className="block text-sm font-medium">Email<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cyan-500" /></label>
            <label className="block text-sm font-medium">Password<input required minLength={8} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cyan-500" /></label>
            <button disabled={loading} className="w-full rounded-xl bg-slate-950 px-4 py-3 font-semibold text-white disabled:opacity-60">{loading ? "Creating account..." : "Create account"}</button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">Already registered? <Link className="font-semibold text-cyan-600" to="/login">Sign in</Link></p>
        </div>
      </div>
    </main>
  );
}
