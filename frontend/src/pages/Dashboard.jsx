import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, ArrowRight, FileText, HeartPulse, LogOut, Pill, ShieldCheck, Stethoscope, ClipboardList } from "lucide-react";
import api from "../services/api";

const tools = [
  { title: "AI Health Chat", description: "Ask health-information questions and receive clear, educational guidance.", icon: HeartPulse, path: "/health-chat" },
  { title: "Symptom Checker", description: "Describe symptoms and receive cautious triage guidance and next steps.", icon: Stethoscope, path: "/symptom-checker" },
  { title: "Medicine Scanner", description: "Understand medicine labels, instructions, warnings, and common side effects.", icon: Pill, path: "/medicine-scanner" },
  { title: "Report Analyzer", description: "Turn complex medical reports into easier-to-understand summaries.", icon: FileText, path: "/report-analyzer" },
];

const eventLabels = { health_chat: "Health chat", symptom_check: "Symptom check", document_analysis: "Document analysis", medication_extraction: "Medication extraction" };
function formatDate(value) { return new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); }

export default function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("carebridge_user") || "{}");
  const [timeline, setTimeline] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api.get("/ai/timeline").then(({ data }) => { if (active) setTimeline(data.timeline || []); }).catch(() => { if (active) setTimeline([]); }).finally(() => { if (active) setTimelineLoading(false); });
    return () => { active = false; };
  }, []);

  const openEvent = (entry) => {
    if (!entry.conversation_id) return;
    localStorage.setItem("carebridge_conversation_id", String(entry.conversation_id));
    navigate("/health-chat");
  };
  const logout = () => { localStorage.removeItem("carebridge_token"); localStorage.removeItem("carebridge_user"); localStorage.removeItem("carebridge_conversation_id"); navigate("/login", { replace: true }); };

  return <main className="min-h-screen bg-slate-50 text-slate-900"><nav className="border-b border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8"><div><p className="text-xl font-bold tracking-tight text-cyan-700">CareBridge AI</p><p className="text-xs text-slate-500">Your healthcare companion</p></div><button onClick={logout} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700"><LogOut size={16} /> Log out</button></div></nav><section className="mx-auto max-w-7xl px-6 py-10 lg:px-8"><div className="rounded-3xl bg-gradient-to-br from-cyan-700 to-blue-800 p-8 text-white shadow-lg sm:p-10"><p className="text-sm font-semibold uppercase tracking-wider text-cyan-100">Patient dashboard</p><h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Hello, {user.name || "there"}.</h1><p className="mt-4 max-w-2xl text-sm leading-6 text-cyan-50 sm:text-base">Access your health-information tools, organize your records, and make more informed healthcare decisions.</p></div><div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{tools.map(({ title, description, icon: Icon, path }) => <article key={title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700"><Icon size={22} /></div><h2 className="mt-5 text-lg font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{description}</p><button onClick={() => navigate(path)} className="mt-5 rounded-full bg-cyan-700 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white">Open tool</button></article>)}</div><div className="mt-8 grid gap-5 md:grid-cols-2"><div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><ClipboardList className="text-cyan-700" size={24} /><div><h2 className="font-semibold">Medication history</h2><p className="text-sm text-slate-500">Review extracted medication records.</p></div></div><button onClick={() => navigate("/medication-history")} className="rounded-full bg-cyan-700 px-4 py-2 text-sm font-semibold text-white">View history</button></div><div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><FileText className="text-cyan-700" size={24} /><div><h2 className="font-semibold">Medical reports</h2><p className="text-sm text-slate-500">Review your analyzed medical documents.</p></div></div><button onClick={() => navigate("/medical-reports")} className="rounded-full bg-cyan-700 px-4 py-2 text-sm font-semibold text-white">View reports</button></div></div><section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center justify-between gap-4"><div><h2 className="text-xl font-semibold">Health timeline</h2><p className="mt-1 text-sm text-slate-500">A structured history of your recent CareBridge activity.</p></div><Activity className="text-cyan-700" size={22} /></div>{timelineLoading ? <p className="mt-6 text-sm text-slate-500">Loading your timeline...</p> : timeline.length === 0 ? <div className="mt-6 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">No health activity yet. Start a health chat, symptom check, or document analysis.</div> : <div className="mt-5 space-y-3">{timeline.map((entry) => <button key={entry.id} disabled={!entry.conversation_id} onClick={() => openEvent(entry)} className="flex w-full items-start justify-between gap-4 rounded-xl border border-slate-200 p-4 text-left transition hover:border-cyan-200 hover:bg-cyan-50/30 disabled:cursor-default"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-cyan-50 px-2.5 py-1 text-xs font-semibold text-cyan-700">{eventLabels[entry.event_type] || entry.event_type}</span><span className="text-xs text-slate-400">{formatDate(entry.created_at)}</span></div><p className="mt-2 font-medium text-slate-900">{entry.title}</p><p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-600">{entry.summary}</p></div>{entry.conversation_id && <ArrowRight className="mt-1 shrink-0 text-cyan-700" size={18} />}</button>)}</div>}</section><div className="mt-8 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900"><ShieldCheck className="mt-0.5 shrink-0" size={20} /><div><h2 className="font-semibold">Your privacy matters</h2><p className="mt-1 text-sm leading-6 text-emerald-800">CareBridge AI provides educational support and does not replace a qualified healthcare professional or emergency services.</p></div></div></section></main>;
}
