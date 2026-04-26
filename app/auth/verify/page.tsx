export default function VerifyRequest() {
  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md border border-[var(--border)] bg-[var(--bg2)] p-8 text-center">
        <h1 className="font-serif text-2xl text-[var(--text)] mb-3">Check your inbox</h1>
        <p className="text-sm text-[var(--text2)]">
          We sent a magic link to your email. Click it to sign in. The link expires in 24 hours.
        </p>
      </div>
    </main>
  );
}
