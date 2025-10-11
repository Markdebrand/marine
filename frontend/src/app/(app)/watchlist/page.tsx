import { Protected } from "@/components/auth/Protected";

export default function WatchlistPage() {
  return (
    <Protected>
      <main className="py-2">
        <header>
          <h1 className="text-3xl font-semibold text-slate-900">Watchlist</h1>
          <p className="text-slate-600 mt-1">Your favorite vessels.</p>
          <div className="mt-4 h-px w-full bg-slate-200" />
        </header>

        <section className="mt-6 grid gap-5 md:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="text-slate-900 font-semibold">No vessels yet</div>
            <p className="text-sm text-slate-600 mt-1">Add a vessel from the Live Map or search by MMSI/IMO/name.</p>
            <div className="mt-4 flex gap-2">
              <a href="/map" className="px-3 py-1.5 text-sm rounded-md bg-red-600 text-white">Go to map</a>
              <a href="/map" className="px-3 py-1.5 text-sm rounded-md border border-slate-300">Search</a>
            </div>
          </div>
        </section>
      </main>
    </Protected>
  );
}
