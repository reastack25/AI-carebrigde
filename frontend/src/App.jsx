import { Link, Route, Routes } from "react-router-dom";

function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-20 lg:px-8">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.25em] text-cyan-400">CareBridge AI</p>
        <h1 className="max-w-4xl text-5xl font-bold tracking-tight sm:text-6xl">
          Healthcare information, made easier to understand.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          An AI-powered healthcare companion designed to help people understand health information and navigate care.
        </p>
        <div className="mt-10 flex gap-4">
          <Link className="rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950" to="/register">
            Get started
          </Link>
          <Link className="rounded-xl border border-slate-700 px-5 py-3 font-semibold" to="/login">
            Sign in
          </Link>
        </div>
        <p className="mt-8 text-sm text-slate-500">CareBridge AI provides educational information and does not replace qualified medical care.</p>
      </section>
    </main>
  );
}

function Placeholder({ title }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        <p className="mt-2 text-slate-600">Phase 1 foundation is ready. Authentication UI will be connected next.</p>
      </section>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Placeholder title="Welcome back" />} />
      <Route path="/register" element={<Placeholder title="Create your account" />} />
    </Routes>
  );
}
