import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const languages = [
  { value: "en", label: "English" },
  { value: "sw", label: "Kiswahili" },
  { value: "luo", label: "Dholuo" },
  { value: "kik", label: "Kikuyu" },
  { value: "kal", label: "Kalenjin" },
];

const urgencyClasses = {
  routine: "bg-emerald-100 text-emerald-800",
  soon: "bg-amber-100 text-amber-800",
  urgent: "bg-orange-100 text-orange-800",
  emergency: "bg-red-100 text-red-800",
};

export default function SymptomChecker() {
  const navigate = useNavigate();
  const [symptoms, setSymptoms] = useState("");
  const [age, setAge] = useState("");
  const [duration, setDuration] = useState("");
  const [language, setLanguage] = useState("en");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const { data } = await api.post("/ai/symptom-check", {
        symptoms,
        age,
        duration,
        language,
        conversation_id: localStorage.getItem("carebridge_conversation_id") || undefined,
      });
      setResult(data.result);
      if (data.conversation?.id) {
        localStorage.setItem("carebridge_conversation_id", String(data.conversation.id));
      }
    } catch (err) {
      setError(err.response?.data?.message || "Unable to complete the symptom check.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8 text-slate-900">
      <div className="mx-auto max-w-3xl">
        <button onClick={() => navigate("/dashboard")} className="text-sm font-medium text-cyan-700">
          ← Back to dashboard
        </button>
        <div className="mt-6 rounded-3xl bg-white p-6 shadow-sm sm:p-8">
          <h1 className="text-3xl font-bold">AI Symptom Checker</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Describe what you are experiencing to receive cautious educational guidance and suggested next steps.
          </p>
          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
            <strong>Important:</strong> CareBridge AI does not diagnose or replace a qualified healthcare professional. If you may be experiencing an emergency, seek immediate medical care.
          </div>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block text-sm font-medium">
              Symptoms
              <textarea
                required
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                maxLength={4000}
                rows={5}
                placeholder="Describe your symptoms, severity, and anything that makes them better or worse..."
                className="mt-2 w-full rounded-xl border border-slate-300 p-3"
              />
              <span className="mt-1 block text-right text-xs text-slate-500">{symptoms.length}/4000</span>
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium">
                Age
                <input value={age} onChange={(e) => setAge(e.target.value)} type="number" min="1" max="120" className="mt-2 w-full rounded-xl border border-slate-300 p-3" />
              </label>
              <label className="block text-sm font-medium">
                Duration
                <input value={duration} onChange={(e) => setDuration(e.target.value)} maxLength={100} placeholder="e.g. 2 days" className="mt-2 w-full rounded-xl border border-slate-300 p-3" />
              </label>
            </div>
            <label className="block text-sm font-medium">
              Response language
              <select value={language} onChange={(e) => setLanguage(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 p-3">
                {languages.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </label>
            <button disabled={loading} className="rounded-xl bg-cyan-700 px-5 py-3 font-semibold text-white disabled:opacity-50">
              {loading ? "Analyzing..." : "Check symptoms"}
            </button>
          </form>

          {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}

          {result && (
            <section className="mt-8 space-y-5 border-t pt-6">
              <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold uppercase ${urgencyClasses[result.urgency] || "bg-slate-100 text-slate-800"}`}>
                Urgency: {result.urgency}
              </span>
              <div>
                <h2 className="font-semibold">Summary</h2>
                <p className="mt-1 text-sm leading-6">{result.summary}</p>
              </div>
              {["possible_explanations", "next_steps", "red_flags"].map((key) => {
                const labels = { possible_explanations: "Possible explanations", next_steps: "Next steps", red_flags: "Red flags" };
                return (
                  <div key={key}>
                    <h2 className="font-semibold">{labels[key]}</h2>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6">
                      {(result[key] || []).map((item, index) => <li key={index}>{item}</li>)}
                    </ul>
                  </div>
                );
              })}
              <p className="rounded-xl bg-slate-100 p-4 text-sm leading-6 text-slate-700">{result.disclaimer}</p>
            </section>
          )}
        </div>
      </div>
    </main>
  );
}
