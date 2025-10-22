import Image from "next/image";

export default function Home() {
  return (
    <section className="py-12">
      <div className="grid md:grid-cols-2 gap-10 items-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            Fuel Price <span className="text-red-600">Intelligence</span>
          </h1>
          <p className="text-zinc-600">
            Check daily prices by product, spot increases and decreases instantly, and navigate directly to charts, tables, and news.
          </p>
          <div className="mt-6 flex gap-4">
            <a href="/services" className="inline-flex items-center rounded-md border px-4 py-2 text-sm font-medium">View demo</a>
          </div>
        </div>
  <div className="rounded-2xl overflow-hidden shadow-sm">
          <Image src="/window.svg" width={800} height={480} alt="Hero" className="w-full h-auto" />
        </div>
      </div>
    </section>
  );
}
