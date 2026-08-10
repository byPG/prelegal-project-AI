"use client";

import Link from "next/link";
import { useAuth } from "@/lib/AuthProvider";

export function AppHeader() {
  const { status, user, signOut } = useAuth();

  return (
    <header className="border-b border-brand-navy/15 bg-white px-6 py-3 sm:px-10">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-6 gap-y-2">
        <div className="flex items-center gap-6">
          <Link href="/" className="font-display text-base font-semibold tracking-tight text-brand-navy">
            Prelegal
          </Link>
          <nav className="flex items-center gap-4 text-sm text-brand-gray">
            <Link href="/" className="transition-colors hover:text-brand-blue">
              Create document
            </Link>
            {status === "authenticated" && (
              <Link href="/documents/" className="transition-colors hover:text-brand-blue">
                My documents
              </Link>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-4 text-sm">
          {status === "loading" && <span className="text-brand-gray">…</span>}
          {status === "unauthenticated" && (
            <>
              <Link href="/login/" className="text-brand-navy transition-colors hover:text-brand-blue">
                Sign in
              </Link>
              <Link
                href="/signup/"
                className="rounded-full bg-brand-purple px-4 py-1.5 font-medium text-white transition-colors hover:bg-brand-purple/90"
              >
                Sign up
              </Link>
            </>
          )}
          {status === "authenticated" && user && (
            <>
              <span className="text-brand-gray">{user.email}</span>
              <button
                type="button"
                onClick={signOut}
                className="text-brand-navy transition-colors hover:text-brand-blue"
              >
                Sign out
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
