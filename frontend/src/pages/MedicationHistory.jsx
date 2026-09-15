import { useEffect, useState } from "react";
import { ArrowLeft, Pill, RefreshCw, ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function formatDate(value) {
  return new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

export default function MedicationHistory() {
  const navigate = useNavigate();
  const [medications, setMedications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadMedications = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/ai/medications");
      setMedications(data.medications || []);
    } catch {
      setError("Unable to load your medication history. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedications();
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xl font-bold tracking-tight text-cyan-700">CareBridge AI</p>
            <p className="text-xs text-slate-500">Medication history</p>
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
            <h1 className="mt-2 text-3xl font-bold tracking-tight">Medication history</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Review medications extracted from documents you have submitted to CareBridge AI.</p>
          </div>
          <button onClick={loadMedications} disabled={loading} className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>

        {error && <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
        {loading ? <p className="mt-8 text-sm text-slate-500">Loading medication history...</p> : medications.length === 0 ? <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center"><Pill className="mx-auto text-cyan-700" size={32} /><h2 className="mt-4 text-lg font-semibold">No medications recorded</h2><p className="mt-2 text-sm text-slate-600">Scan a prescription or medicine document to create your first record.</p><button onClick={() => navigate("/medicine-scanner")} className="mt-5 rounded-full bg-cyan-700 px-5 py-2 text-sm font-semibold text-white">Open medicine scanner</button></div> : <div className="mt-8 grid gap-5 md:grid-cols-2">{medications.map((medication) => <article key={medication.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start gap-3"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700"><Pill size={22} /></div><div className="min-w-0"><h2 className="text-lg font-semibold">{medication.name}</h2><p className="mt-1 text-xs text-slate-500">Recorded {formatDate(medication.created_at)}</p></div></div><dl className="mt-5 space-y-3 text-sm"><div><dt className="font-semibold text-slate-700">Dosage</dt><dd className="text-slate-600">{medication.dosage || "Not specified"}</dd></div><div><dt className="font-semibold text-slate-700">Frequency</dt><dd className="text-slate-600">{medication.frequency || "Not specified"}</dd></div><div><dt className="font-semibold text-slate-700">Duration</dt><dd className="text-slate-600">{medication.duration || "Not specified"}</dd></div><div><dt className="font-semibold text-slate-700">Instructions</dt><dd className="whitespace-pre-wrap text-slate-600">{medication.instructions || "Not specified"}</dd></div></dl>{medication.warnings?.length > 0 && <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4"><div className="flex items-center gap-2 text-sm font-semibold text-amber-900"><ShieldAlert size={16} /> Warnings</div><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">{medication.warnings.map((warning, index) => <li key={`${medication.id}-warning-${index}`}>{warning}</li>)}</ul></div>}</article>)}</div>}

        <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm leading-6 text-emerald-900">CareBridge AI provides educational information only. Do not start, stop, or change medication based only on this history; confirm instructions with a qualified healthcare professional.</div>
      </section>
    </main>
  );
}
