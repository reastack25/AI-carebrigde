import { useEffect, useMemo, useState } from "react";
import { Activity, ArrowLeft, FileText, Pill, RefreshCw, ShieldAlert, Stethoscope, Clock3 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const filters = ["all", "medications", "reports", "symptoms", "timeline"];

function formatDate(value) {
  return new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function RecordCard({ type, item }) {
  const config = {
    medications: { label: "Medication", icon: Pill, badge: "bg-cyan-50 text-cyan-700" },
    reports: { label: "Medical report", icon: FileText, badge: "bg-blue-50 text-blue-700" },
    symptoms: { label: "Symptom check", icon: Stethoscope, badge: "bg-amber-50 text-amber-700" },
    timeline: { label: "Timeline event", icon: Clock3, badge: "bg-violet-50 text-violet-700" },
  }[type];
  const Icon = config.icon;
  const title = type === "medications" ? item.name : type === "reports" ? item.filename : item.title || "Symptom check";
  const summary = type === "medications"
    ? [item.dosage, item.frequency, item.duration].filter(Boolean).join(" · ") || "Medication details not specified"
    : item.summary || "No summary available";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${config.badge}`}><Icon size={20} /></div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${config.badge}`}>{config.label}</span>
            <span className="text-xs text-slate-400">{formatDate(item.created_at)}</span>
          </div>
          <h2 className="mt-3 break-words font-semibold text-slate-900">{title}</h2>
          {type === "symptoms" && <p className="mt-1 text-xs text-slate-500">Urgency: {item.urgency || "Not specified"}</p>}
          {type === "timeline" && item.event_type && <p className="mt-1 text-xs text-slate-500">Event: {item.event_type.replaceAll("_", " ")}</p>}
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{summary}</p>
          {type === "medications" && item.instructions && <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600"><strong>Instructions:</strong> {item.instructions}</p>}
          {type === "medications" && item.warnings?.length > 0 && <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"><strong>Warnings:</strong> {item.warnings.join("; ")}</div>}
          {type === "symptoms" && item.red_flags?.length > 0 && <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800"><strong>Red flags:</strong> {item.red_flags.join("; ")}</div>}
        </div>
      </div>
    </article>
  );
}

export default function HealthRecords() {
  const navigate = useNavigate();
  const [records, setRecords] = useState({ medications: [], reports: [], symptoms: [], timeline: [] });
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRecords = async () => {
    setLoading(true);
    setError("");
    try {
      const [medications, reports, symptoms, timeline] = await Promise.all([
        api.get("/ai/medications"),
        api.get("/ai/medical-reports"),
        api.get("/ai/symptom-checks"),
        api.get("/ai/timeline"),
      ]);
      setRecords({
        medications: medications.data.medications || [],
        reports: reports.data.medical_reports || [],
        symptoms: symptoms.data.symptom_checks || [],
        timeline: timeline.data.timeline || [],
      });
    } catch {
      setError("Unable to load your health records. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadRecords(); }, []);

  const visibleRecords = useMemo(() => {
    const groups = filter === "all" ? filters.slice(1) : [filter];
    return groups.flatMap((type) => records[type].map((item) => ({ type, item })))
      .sort((a, b) => new Date(b.item.created_at) - new Date(a.item.created_at));
  }, [filter, records]);

  const counts = Object.fromEntries(filters.slice(1).map((type) => [type, records[type].length]));

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div><p className="text-xl font-bold tracking-tight text-cyan-700">CareBridge AI</p><p className="text-xs text-slate-500">Unified health records</p></div>
          <button onClick={() => navigate("/dashboard")} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700"><ArrowLeft size={16} /> Dashboard</button>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><p className="text-sm font-semibold uppercase tracking-wider text-cyan-700">Your health data</p><h1 className="mt-2 text-3xl font-bold tracking-tight">Health records</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">One place to review medications, medical reports, symptom checks, and your complete CareBridge activity timeline.</p></div>
          <button onClick={loadRecords} disabled={loading} className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60"><RefreshCw size={16} /> Refresh</button>
        </div>

        <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {filters.map((value) => <button key={value} onClick={() => setFilter(value)} className={`rounded-xl border p-4 text-left transition ${filter === value ? "border-cyan-600 bg-cyan-50" : "border-slate-200 bg-white hover:border-cyan-200"}`}><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{value === "all" ? "All records" : value}</p><p className="mt-1 text-2xl font-bold">{value === "all" ? counts.medications + counts.reports + counts.symptoms + counts.timeline : counts[value]}</p></button>)}
        </div>

        {error && <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
        {loading ? <p className="mt-8 text-sm text-slate-500">Loading your health records...</p> : visibleRecords.length === 0 ? <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center"><Activity className="mx-auto text-cyan-700" size={34} /><h2 className="mt-4 text-lg font-semibold">No records yet</h2><p className="mt-2 text-sm text-slate-600">Use CareBridge AI's health tools to build your record history.</p></div> : <div className="mt-8 grid gap-5 lg:grid-cols-2">{visibleRecords.map(({ type, item }) => <RecordCard key={`${type}-${item.id}`} type={type} item={item} />)}</div>}

        <div className="mt-8 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900"><ShieldAlert className="mt-0.5 shrink-0" size={20} /><p>CareBridge AI records are educational support and may contain errors. They are not a diagnosis or a substitute for professional medical care. Seek qualified medical advice for treatment decisions or urgent symptoms.</p></div>
      </section>
    </main>
  );
}
