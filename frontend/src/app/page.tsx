import Image from "next/image";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4">
        <section className="py-12">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
