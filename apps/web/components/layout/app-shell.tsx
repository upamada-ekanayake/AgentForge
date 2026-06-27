import Link from "next/link";
import type { ReactNode } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/workspaces", label: "Workspaces" },
  { href: "/documents", label: "Documents" },
  { href: "/internships", label: "Internships" },
  { href: "/internship-match", label: "Internship Match" },
  { href: "/internship-rank", label: "Internship Rank" },
  { href: "/agent-runs", label: "Agent Runs" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex min-h-16 max-w-6xl flex-col gap-3 px-6 py-4 md:flex-row md:items-center md:justify-between md:py-0">
          <Link href="/dashboard" className="text-lg font-semibold">
            AgentForge
          </Link>
          <nav className="flex max-w-full items-center gap-5 overflow-x-auto whitespace-nowrap text-sm text-muted-foreground">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="transition-colors hover:text-foreground"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
    </div>
  );
}
