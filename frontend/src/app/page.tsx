import { Navbar } from "@/app/(home)/components/Navbar";
import { Footer } from "@/app/(home)/components/Footer";
import HomePage from "@/app/(home)/page";

export default function RootHomeWrapper() {
  // Este archivo actúa como wrapper: mantiene Navbar y Footer, y renderiza
  // el verdadero Home que vive en `src/app/(home)/page.tsx`.
  return (
    <>
      <Navbar />
      <main>
        <HomePage />
      </main>
      <Footer />
    </>
  );
}
