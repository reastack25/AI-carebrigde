import { useNavigate } from "react-router-dom";
import { Activity, FileText, HeartPulse, LogOut, Pill, ShieldCheck } from "lucide-react";

const tools = [
  {
    title: "AI Health Chat",
    description: "Ask health-information questions and receive clear, educational guidance.",
    icon: HeartPulse,
    path: "/health-chat",
    active: true,
  },
  {
    title: "Medicine Scanner",
    description: "Understand medicine labels, instructions, warnings, and common side effects.",
    icon: Pill,
    active: false,
  },
  {
    title: "Report Analyzer",
    description: "Turn complex medical reports into easier-to-understand summaries.",
    icon: FileText,
    active: false,
  },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("carebridge_user") || "{}");

  const logout = () => {
    localStorage.removeItem("carebridge_token");
    localStorage.removeItem("carebridge_user");
    navigate("/login", { replace: true });
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
          <div><p className="text-xl font-bold tracking-tight text-cyan-700">CareBridge AI</p><p className="text-xs text-slate-500">Your healthcare companion</p></div>
          <button onClick={logout} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"><LogOut size={16} /> Log out</button>
        </div>
      </nav>

      <section className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
        <div className="rounded-3xl bg-gradient-to-br from-cyan-700 to-blue-800 p-8 text-white shadow-lg sm:p-10">
          <p className="text-sm font-semibold uppercase tracking-wider text-cyan-100">Patient dashboard</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Hello, {user.name || "there"}.</h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-cyan-50 sm:text-base">Access your health-information tools, organize your records, and make more informed healthcare decisions.</p>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {tools.map(({ title, description, icon: Icon, path, active }) => (
            <article key={title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700"><Icon size={22} /></div>
              <h2 className="mt-5 text-lg font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
              {active ? <button onClick={() => navigate(path)} className="mt-5 rounded-full bg-cyan-700 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white hover:bg-cyan-800">Open tool</button> : <span className="mt-5 inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Coming next</span>}
            </article>
          ))}
        </div>

        <div className="mt-8 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900"><ShieldCheck className="mt-0.5 shrink-0" size={20} /><div><h2 className="font-semibold">Your privacy matters</h2><p className="mt-1 text-sm leading-6 text-emerald-800">CareBridge AI provides educational support and does not replace a qualified healthcare professional or emergency services.</p></div></div>
        <div className="mt-8 flex items-center gap-3 text-sm text-slate-500"><Activity size={18} /><span>Your secure workspace is ready for the next development phase.</span></div>
      </section>
    </main>
  );
}
