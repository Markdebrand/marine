import { Protected } from "@/components/auth/Protected";

export default function WatchlistPage() {
  return (
    <Protected>
      <main className="container mx-auto p-6">
        <h1 className="text-2xl font-semibold">Watchlist</h1>
        <p className="text-zinc-600 mt-2">Tus embarcaciones favoritas.</p>
      </main>
    </Protected>
  );
}
