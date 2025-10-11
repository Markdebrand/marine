import AppHeader from "@/components/AppHeader";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <AppHeader />
      <div className="mx-auto max-w-7xl px-6 py-6">
        {children}
      </div>
    </div>
  );
}
