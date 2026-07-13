import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Handle logout cleanup here (clearing tokens, etc.)
    
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-700">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white/90 p-5 shadow-[0_12px_30px_rgba(15,23,42,0.08)] backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-blue-600">Career Mentor Companion</p>
            <h1 className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl">Dashboard</h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-500">
              Keep track of your practice sessions, review weak areas, and stay focused on the next step.
            </p>
          </div>

          <button
            onClick={handleLogout}
            className="inline-flex items-center justify-center rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            Log Out
          </button>
        </header>

        <main className="flex-1 space-y-6">
          <section className="grid gap-6 rounded-[28px] bg-gradient-to-br from-blue-100 via-white to-transparent p-6 shadow-[0_18px_40px_rgba(15,23,42,0.08)] lg:grid-cols-[1.7fr_1fr] lg:p-8">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.24em] text-blue-600">Smart career support</p>
              <h2 className="mt-3 max-w-2xl text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
                Prepare with structure, then improve with every session.
              </h2>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                Use your dashboard to review interview history, focus on weak spots, and keep a steady rhythm of practice.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <button className="rounded-full bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700">
                  Start New Practice
                </button>
                <button className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:text-blue-700">
                  Review Weak Areas
                </button>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold text-slate-500">Progress snapshot</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Mock interviews</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">18</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Improvement streak</p>
                  <p className="mt-2 text-3xl font-bold text-slate-900">7 days</p>
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            {[
              ['Answered questions', '128', 'Blue'],
              ['Weak areas reduced', '4', 'Green'],
              ['Sessions completed', '22', 'Amber'],
            ].map(([label, value, tone]) => (
              <article
                key={label}
                className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <p className="text-sm font-medium text-slate-500">{label}</p>
                <div className="mt-4 flex items-end justify-between gap-4">
                  <p className="text-4xl font-bold tracking-tight text-slate-900">{value}</p>
                  <span
                    className={
                      tone === 'Blue'
                        ? 'rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700'
                        : tone === 'Green'
                          ? 'rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700'
                          : 'rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700'
                    }
                  >
                    +12%
                  </span>
                </div>
              </article>
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">Recent activity</h3>
              <div className="mt-5 space-y-4">
                {[
                  ['Technical round practice completed', '2 hours ago'],
                  ['Added behavioral interview notes', 'Yesterday'],
                  ['Reviewed communication weak area', '2 days ago'],
                ].map(([title, time]) => (
                  <div key={title} className="flex items-start justify-between gap-4 rounded-2xl bg-slate-50 p-4">
                    <div>
                      <p className="font-semibold text-slate-900">{title}</p>
                      <p className="mt-1 text-sm text-slate-500">Keep building on the last session.</p>
                    </div>
                    <span className="shrink-0 text-sm text-slate-400">{time}</span>
                  </div>
                ))}
              </div>
            </article>

            <aside className="rounded-3xl border border-slate-200 bg-slate-900 p-6 text-white shadow-sm">
              <p className="text-xs font-bold uppercase tracking-[0.24em] text-blue-300">Next actions</p>
              <h3 className="mt-3 text-2xl font-bold">Keep momentum going</h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                Pick one focused activity and finish it before moving on. Small, consistent practice compounds fast.
              </p>

              <div className="mt-6 space-y-3">
                <button className="w-full rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100">
                  Practice a new question set
                </button>
                <button className="w-full rounded-2xl border border-white/15 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
                  View session history
                </button>
              </div>
            </aside>
          </section>
        </main>
      </div>
    </div>
  );
}