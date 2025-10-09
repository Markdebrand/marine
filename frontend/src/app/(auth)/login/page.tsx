"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { setToken } = useAuth();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Static login
      const isValid = email === "admin@example.com" && password === "admin123";
      if (!isValid) throw new Error("Invalid credentials");
      const fakeToken = "static-dev-token";
      setToken(fakeToken);
      router.replace("/map");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="min-h-screen grid md:grid-cols-2">
      <div className="relative hidden md:block">
        <div className="absolute inset-0" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=2070&auto=format&fit=crop)', backgroundSize: 'cover', backgroundPosition: 'center' }} />
  <div className="absolute inset-0 bg-white/40" />
      </div>
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-md rounded-2xl bg-white/80 backdrop-blur p-6 shadow-lg">
          <div className="mb-6">
            <div className="flex items-center gap-2 text-xl font-bold"><span className="inline-block h-6 w-6 rounded bg-red-600" /> HSO MARINE</div>
            <p className="text-zinc-500 text-sm">Welcome back</p>
          </div>
          <form className="grid gap-4" onSubmit={onSubmit}>
            <input className="border rounded p-2" placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input className="border rounded p-2" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            {error && <p className="text-red-600 text-sm">{error}</p>}
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2"><input type="checkbox" /> Remember me</label>
              <a href="#" className="text-zinc-600 hover:underline">Forgot password?</a>
            </div>
            <button className="inline-flex items-center rounded-md bg-red-600 px-4 py-2 text-white text-sm font-medium hover:bg-red-700" disabled={loading}>
              {loading ? "Signing in…" : "LOG IN"}
            </button>
          </form>
          <div className="text-sm text-zinc-600 mt-4">
            Don’t have an account? <a href="#" className="hover:underline">Sign up</a>
          </div>
        </div>
      </div>
    </section>
  );
}
