import { useEffect, useState } from "react";
import { ArrowLeft, ClipboardCheck, Lock, RefreshCw, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const formatDate = (value) => new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });

export default function ClinicalReview() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("carebridge_user") || "{}");
  const isDoctor = user.role === "doctor";
  const [doctors, setDoctors] = useState([]);
  const [consents, setConsents] = useState([]);
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [records, setRecords] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [note, setNote] = useState("");
  const [status, setStatus] = useState("reviewed");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPatientData = async () => {
    setLoading(true); setError("");
    try {
      const requests = [api.get("/clinical/reviews")];
      if (isDoctor) requests.push(api.get("/clinical/patients"));
      else requests.push(api.get("/clinical/doctors"), api.get("/clinical/consents"));
      const responses = await Promise.all(requests);
      setReviews(responses[0].data.reviews || []);
      if (isDoctor) setPatients(responses[1].data.patients || []);
      else { setDoctors(responses[1].data.doctors || []); setConsents(responses[2].data.consents || []); }
    } catch (requestError) { setError(requestError.response?.data?.message || "Unable to load clinical review data."); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadPatientData(); }, []);

  const grantConsent = async (doctorId) => {
    try { await api.post("/clinical/consents", { doctor_id: doctorId }); await loadPatientData(); }
    catch (requestError) { setError(requestError.response?.data?.message || "Unable to grant consent."); }
  };

  const revokeConsent = async (doctorId) => {
    try { await api.delete(`/clinical/consents/${doctorId}`); await loadPatientData(); }
    catch (requestError) { setError(requestError.response?.data?.message || "Unable to revoke consent."); }
  };

  const selectPatient = async (patient) => {
    setSelectedPatient(patient); setRecords(null); setError("");
    try { const { data } = await api.get(`/clinical/patients/${patient.id}/records`); setRecords(data.records); }
    catch (requestError) { setError(requestError.response?.data?.message || "Unable to load patient records."); }
  };

  const submitReview = async (event) => {
    event.preventDefault();
    if (!selectedPatient || !note.trim()) return;
    try {
      await api.post(`/clinical/patients/${selectedPatient.id}/reviews`, { note: note.trim(), status });
      setNote(""); setStatus("reviewed"); await loadPatientData();
    } catch (requestError) { setError(requestError.response?.data?.message || "Unable to save clinical review."); }
  };

  return <main className="min-h-screen bg-slate-50 text-slate-900"><nav className="border-b border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4"><button onClick={() => navigate("/dashboard")} className="inline-flex items-center gap-2 text-sm font-medium text-slate-600"><ArrowLeft size={17} /> Dashboard</button><button onClick={loadPatientData} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium"><RefreshCw size={16} /> Refresh</button></div></nav><section className="mx-auto max-w-7xl px-6 py-8"><div className="rounded-3xl bg-gradient-to-br from-cyan-700 to-blue-800 p-8 text-white"><p className="text-sm font-semibold uppercase tracking-wider text-cyan-100">{isDoctor ? "Clinical workspace" : "Care team access"}</p><h1 className="mt-2 text-3xl font-bold">{isDoctor ? "Patient clinical reviews" : "Share records with your doctor"}</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-cyan-50">{isDoctor ? "Review patient records only after explicit consent, then add clinician-authored notes." : "You control which doctors can access your CareBridge health records. Consent can be revoked at any time."}</p></div>{error && <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}{loading ? <p className="mt-8 text-sm text-slate-500">Loading...</p> : isDoctor ? <div className="mt-8 grid gap-6 lg:grid-cols-[280px_1fr]"><aside className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Patients with consent</h2><div className="mt-4 space-y-2">{patients.length === 0 ? <p className="text-sm text-slate-500">No patients have granted access.</p> : patients.map((patient) => <button key={patient.id} onClick={() => selectPatient(patient)} className={`w-full rounded-xl p-3 text-left text-sm ${selectedPatient?.id === patient.id ? "bg-cyan-50 text-cyan-800" : "hover:bg-slate-50"}`}><p className="font-semibold">{patient.name}</p><p className="text-xs text-slate-500">{patient.email}</p></button>)}</div></aside><section className="space-y-6">{selectedPatient && <><div className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">{selectedPatient.name}'s records</h2>{records ? <div className="mt-5 grid gap-4 sm:grid-cols-3"><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Medications</p><p className="mt-1 text-2xl font-bold">{records.medications.length}</p></div><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Medical reports</p><p className="mt-1 text-2xl font-bold">{records.medical_reports.length}</p></div><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Symptom checks</p><p className="mt-1 text-2xl font-bold">{records.symptom_checks.length}</p></div></div> : <p className="mt-4 text-sm text-slate-500">Select a patient to load records.</p>}</div><form onSubmit={submitReview} className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">Add clinical note</h2><textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength={5000} rows={5} className="mt-4 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-cyan-600" placeholder="Document your clinical review..." required /><div className="mt-4 flex flex-wrap gap-3"><select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm"><option value="reviewed">Reviewed</option><option value="follow_up">Follow-up</option><option value="urgent_review">Urgent review</option></select><button className="rounded-lg bg-cyan-700 px-5 py-2 text-sm font-semibold text-white">Save review</button></div></form></>}</section></div> : <div className="mt-8 grid gap-6 lg:grid-cols-2"><section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">Available doctors</h2><div className="mt-5 space-y-3">{doctors.length === 0 ? <p className="text-sm text-slate-500">No doctors are registered yet.</p> : doctors.map((doctor) => { const active = consents.some((item) => item.doctor_id === doctor.id && item.active); return <div key={doctor.id} className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 p-4"><div><p className="font-semibold">{doctor.name}</p><p className="text-xs text-slate-500">{doctor.email}</p></div>{active ? <button onClick={() => revokeConsent(doctor.id)} className="rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-700">Revoke</button> : <button onClick={() => grantConsent(doctor.id)} className="rounded-lg bg-cyan-700 px-3 py-2 text-xs font-semibold text-white">Grant access</button>}</div>; })}</div></section><section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">Doctor reviews</h2><div className="mt-5 space-y-3">{reviews.length === 0 ? <p className="text-sm text-slate-500">No clinical reviews yet.</p> : reviews.map((review) => <article key={review.id} className="rounded-xl border border-slate-200 p-4"><div className="flex items-center justify-between gap-3"><span className="rounded-full bg-cyan-50 px-2.5 py-1 text-xs font-semibold text-cyan-700">{review.status.replace("_", " ")}</span><span className="text-xs text-slate-400">{formatDate(review.created_at)}</span></div><p className="mt-3 text-sm leading-6 text-slate-700">{review.note}</p></article>)}</div></section></div>}<div className="mt-8 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-900"><Lock size={20} className="mt-0.5 shrink-0" /><div><h2 className="font-semibold">Consent and safety</h2><p className="mt-1 text-sm leading-6">Doctors can access records only while your consent is active. Clinical notes are authored by the doctor; CareBridge AI does not replace professional medical judgment.</p></div></div></section></main>;
}
