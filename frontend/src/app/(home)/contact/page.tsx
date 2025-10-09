export default function ContactPage() {
  return (
    <section className="py-12">
      <h1 className="text-3xl font-semibold mb-4">Contact Us</h1>
      <p className="text-zinc-600 mb-6">We would love to hear from you. Send us a message and we will get back to you soon.</p>
      <form className="grid gap-4 max-w-xl">
        <input className="border rounded p-2" placeholder="Your name" />
        <input className="border rounded p-2" placeholder="Email" type="email" />
        <textarea className="border rounded p-2 min-h-32" placeholder="Message" />
        <button className="inline-flex items-center rounded-md bg-red-600 px-4 py-2 text-white text-sm font-medium hover:bg-red-700 w-fit">Send</button>
      </form>
    </section>
  );
}
