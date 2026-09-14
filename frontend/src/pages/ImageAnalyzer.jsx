import { useState } from "react";
import { ArrowLeft, FileImage, FileText, LoaderCircle, Send, ShieldCheck, Upload } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";

const configurations = {
  "/medicine-scanner": {
    title: "Medicine Scanner",
    eyebrow: "Medication support",
    description: "Upload a clear photo of a medicine label or package to understand its visible information.",
    instruction: "Explain the medicine name, visible dosage instructions, common uses, warnings, and possible side effects. Do not prescribe or recommend a dose.",
    accept: "image/jpeg,image/png,image/webp,image/heic,image/heif",
    fileHint: "Choose a JPG, PNG, WEBP, HEIC, or HEIF image",
    actionLabel: "Analyze image",
  },
  "/report-analyzer": {
    title: "Report Analyzer",
    eyebrow: "Medical report support",
    description: "Upload a clear image or PDF of a medical report to receive a plain-language educational summary.",
    instruction: "Summarize the visible report in plain language, explain medical terms, identify values that may need discussion with a clinician, and state when the document is unclear. Do not diagnose.",
    accept: "image/jpeg,image/png,image/webp,image/heic,image/heif,application/pdf",
    fileHint: "Choose an image or PDF medical report",
    actionLabel: "Analyze report",
  },
};

export default function ImageAnalyzer() {
  const navigate = useNavigate();
  const location = useLocation();
  const config = configurations[location.pathname] || configurations["/medicine-scanner"];
  const [file, setFile] = useState(null);
  const [instruction, setInstruction] = useState(config.instruction);
  const [language, setLanguage] = useState("en");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyze = async (event) => {
    event.preventDefault();
    if (!file) return setError("Please select a file first.");
    setLoading(true);
    setError("");
    setResponse("");
    const formData = new FormData();
    formData.append("image", file);
    formData.append("instruction", instruction);
    formData.append("language", language);

    try {
      const result = await api.post("/ai/analyze-image", formData);
      setResponse(result.data.response);
    } catch (err) {
      setError(err.response?.data?.message || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <button onClick={() => navigate("/dashboard")} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-cyan-700"><ArrowLeft size={17} /> Dashboard</button>
          <p className="font-bold text-cyan-700">CareBridge AI</p>
        </div>
      </nav>

      <section className="mx-auto max-w-5xl px-6 py-10">
        <div className="rounded-3xl bg-gradient-to-br from-cyan-700 to-blue-800 p-8 text-white sm:p-10">
          <p className="text-sm font-semibold uppercase tracking-wider text-cyan-100">{config.eyebrow}</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">{config.title}</h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-cyan-50">{config.description}</p>
        </div>

        <form onSubmit={analyze} className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <label className="block text-sm font-semibold text-slate-800">Upload file</label>
          <label className="mt-3 flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center hover:border-cyan-500">
            <Upload className="text-cyan-700" size={28} />
            <span className="mt-3 text-sm font-semibold">{file ? file.name : config.fileHint}</span>
            <span className="mt-1 text-xs text-slate-500">Maximum file size: 10 MB</span>
            <input type="file" accept={config.accept} onChange={(event) => setFile(event.target.files?.[0] || null)} className="sr-only" />
          </label>

          <div className="mt-6 grid gap-5 md:grid-cols-2">
            <label className="block text-sm font-semibold">Response language
              <select value={language} onChange={(event) => setLanguage(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-3 text-sm font-normal">
                <option value="en">English</option><option value="sw">Kiswahili</option><option value="luo">Dholuo</option><option value="kik">Kikuyu</option><option value="kal">Kalenjin</option>
              </select>
            </label>
            <label className="block text-sm font-semibold">Analysis instruction
              <textarea value={instruction} onChange={(event) => setInstruction(event.target.value)} rows={4} className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-3 text-sm font-normal" />
            </label>
          </div>

          {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button disabled={loading} className="mt-6 inline-flex items-center gap-2 rounded-full bg-cyan-700 px-5 py-3 text-sm font-semibold text-white hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-60">{loading ? <LoaderCircle className="animate-spin" size={17} /> : <Send size={17} />} {loading ? "Analyzing..." : config.actionLabel}</button>
        </form>

        {response && <section className="mt-8 rounded-2xl border border-cyan-200 bg-white p-6 shadow-sm sm:p-8"><div className="flex items-center gap-2 text-cyan-700">{file?.type === "application/pdf" ? <FileText size={20} /> : <FileImage size={20} />}<h2 className="font-semibold">Analysis result</h2></div><div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">{response}</div></section>}
        <div className="mt-8 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900"><ShieldCheck className="mt-0.5 shrink-0" size={20} /><p className="text-sm leading-6">This tool provides educational information only. It cannot confirm a diagnosis, replace a clinician, or handle emergencies.</p></div>
      </section>
    </main>
  );
}
