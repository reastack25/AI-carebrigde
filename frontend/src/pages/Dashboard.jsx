import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("carebridge_user") || "{}");

  const logout = () => {
    localStorage.removeItem("carebridge_token");
    localStorage.removeItem("carebridge_user");
    navigate("/login", { replace: true });
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <nav className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <span className="font-bold text-slate-950">CareBridge AI</span>
          <button onClick={logout} className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium">Log out</button>
        </div>
      </nav>
      <section className="mx-auto max-w-6xl px-6 py-12">
        <p className="text-sm font-medium text-cyan-600">Patient dashboard</p>
        <h1 className="mt-2 text-4xl font-bold text-slate-950">Hello, {user.name || "there"}.</h1>
        <p className="mt-3 max-w-2xl text-slate-600">Your secure CareBridge workspace is ready. AI health tools will be added in the next phase.</p>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {[["AI Health Chat", "Ask health-information questions."], ["Medicine Scanner", "Understand medicine labels and instructions."], ["Report Analyzer", "Turn complex health reports into plain language."]].map(([title, text]) => (
            <article key={title} className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="font-semibold text-slate-900">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">{text}</p>
              <span className="mt-5 inline-block text-xs font-semibold uppercase tracking-wide text-slate-400">Coming next</span>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
