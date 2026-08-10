"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ChatApiError } from "@/lib/api";
import { useAuth } from "@/lib/AuthProvider";

export default function LoginPage() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await signIn(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Couldn't sign in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex max-w-md flex-col gap-6 px-6 py-16 sm:px-10">
      <div>
        <h1 className="font-display text-2xl font-semibold text-brand-navy">Sign in</h1>
        <p className="mt-1 text-sm text-brand-gray">
          New here?{" "}
          <Link href="/signup/" className="text-brand-blue hover:underline">
            Create an account
          </Link>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm text-brand-navy">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-brand-navy/20 px-3 py-2 text-sm focus:border-brand-blue focus:outline-none"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-brand-navy">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-brand-navy/20 px-3 py-2 text-sm focus:border-brand-blue focus:outline-none"
          />
        </label>

        {error && <p className="text-sm text-brand-danger">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 rounded-full bg-brand-purple px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-purple/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
