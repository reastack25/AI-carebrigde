import { useState } from "react";
import { ArrowLeft, HeartPulse, LoaderCircle, Send, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function HealthChat() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submitMessage = async (event) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || loading) return;

    setMessages((current) => [...current, { role: "user", text: trimmed }]);
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await api.post("/ai/chat", { message: trimmed });
      setMessages((current) => [...current, { role: "assistant", text: response.data.response }]);
    } catch (requestError) {
      setError(requestError.response?.data?.message || "The AI service is temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <button onClick={() => navigate("/dashboard")} className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-cyan-700">
            <ArrowLeft size={17} /> Back to dashboard
          </button>
          <div className="flex items-center gap-2 font-bold text-cyan-700"><HeartPulse size={20} /> CareBridge AI</div>
        </div>
      </nav>

      <section className="mx-auto flex max-w-4xl flex-col px-6 py-8">
        <div className="rounded-3xl bg-gradient-to-br from-cyan-700 to-blue-800 p-7 text-white">
          <p className="text-sm font-semibold uppercase tracking-wider text-cyan-100">AI health chat</p>
          <h1 className="mt-2 text-3xl font-bold">Ask a health-information question</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-cyan-50">Receive cautious, educational information in plain language. CareBridge AI does not diagnose or prescribe.</p>
        </div>

        <div className="mt-6 min-h-80 space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          {messages.length === 0 && <p className="py-16 text-center text-sm text-slate-500">Your conversation will appear here.</p>}
          {messages.map((item, index) => (
            <div key={`${item.role}-${index}`} className={`flex ${item.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 ${item.role === "user" ? "bg-cyan-700 text-white" : "bg-slate-100 text-slate-800"}`}>{item.text}</div>
            </div>
          ))}
          {loading && <div className="flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={17} /> CareBridge is thinking...</div>}
          {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </div>

        <form onSubmit={submitMessage} className="mt-4 flex gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
          <input value={message} onChange={(event) => setMessage(event.target.value)} maxLength={4000} placeholder="For example: What are common causes of a headache?" className="min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100" />
          <button disabled={loading || !message.trim()} className="inline-flex items-center gap-2 rounded-xl bg-cyan-700 px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"><Send size={17} /> Send</button>
        </form>

        <div className="mt-5 flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900"><ShieldCheck size={18} className="mt-1 shrink-0" /> Seek urgent medical care for severe or life-threatening symptoms. Do not use this chat as a substitute for a clinician.</div>
      </section>
    </main>
  );
}
