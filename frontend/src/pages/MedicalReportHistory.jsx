import { useEffect, useState } from "react";
import { ArrowLeft, FileText, RefreshCw, ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function formatDate(value) {
  return new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function documentType(report) {
  if (report.mime_type === "application/pdf") return "PDF document";
  if (report.mime_type.startsWith("image/")) return "Image document";
  return "Medical document";
}

export default function MedicalReportHistory() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReports = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/ai/medical-reports");
      setReports(data.medical_reports || []);
    } catch {
      setError("Unable to load your medical report history. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xl font-bold tracking-tight text-cyan-700">CareBridge AI</p>
            <p className="text-xs text-slate-500">Medical report history</p>
          </div>
          <button onClick={() => navigate("/dashboard")} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700">
            <ArrowLeft size={16} /> Dashboard
          </button>
        </div>
      </nav>

      <section className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-cyan-700">Your records</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">Medical report history</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Review AI-generated summaries of medical documents you have previously submitted.</p>
          </div>
          <button onClick={loadReports} disabled={loading} className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>

        {error && <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}

        {loading ? <p className="mt-8 text-sm text-slate-500">Loading medical report history...</p> : reports.length === 0 ? <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center"><FileText className="mx-auto text-cyan-700" size={32} /><h2 className="mt-4 text-lg font-semibold">No medical reports recorded</h2><p className="mt-2 text-sm text-slate-600">Analyze a lab report, prescription, or other supported medical document to create your first record.</p><button onClick={() => navigate("/report-analyzer")} className="mt-5 rounded-full bg-cyan-700 px-5 py-2 text-sm font-semibold text-white">Open report analyzer</button></div> : <div className="space-y-5 mt-8">{reports.map((report) => <article key={report.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div className="flex items-start gap-3"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700"><FileText size={22} /></div><div className="min-w-0"><h2 className="break-words text-lg font-semibold">{report.filename}</h2><p className="mt-1 text-xs text-slate-500">{documentType(report)} · Analyzed {formatDate(report.created_at)}</p></div></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">{report.language || "en"}</span></div>{report.instruction && <div className="mt-5 rounded-xl bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Analysis request</p><p className="mt-1 text-sm text-slate-700">{report.instruction}</p></div>}<div className="mt-5"><h3 className="text-sm font-semibold text-slate-700">AI summary</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-600">{report.summary}</p></div></article>)}</div>}

        <div className="mt-8 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900"><ShieldAlert className="mt-0.5 shrink-0" size={20} /><p>CareBridge AI summaries are educational and may contain errors. They are not a diagnosis. Discuss results and treatment decisions with a qualified healthcare professional, especially when symptoms are severe or worsening.</p></div>
      </section>
    </main>
  );
}
