import { Protected } from "@/components/auth/Protected";

export default function MapPage() {
  return (
    <Protected>
      <main className="container mx-auto p-6">
        <h1 className="text-2xl font-semibold">Map</h1>
        <p className="text-zinc-600 mt-2">Private view for the vessel map.</p>
      </main>
    </Protected>
  );
}
