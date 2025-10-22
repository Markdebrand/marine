import type { ReactNode } from "react";
import { Navbar } from "@/app/(home)/components/Navbar";
import { Footer } from "@/app/(home)/components/Footer";

export default function HomeGroupLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4">{children}</main>
      <Footer />
    </>
  );
}
