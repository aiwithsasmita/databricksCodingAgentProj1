"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/* Page switcher embedded in the shared Header: Chat (/) and Architecture
 * (/architecture). The active tab is derived from the current pathname. */
const TABS = [
  { href: "/", label: "Chat" },
  { href: "/architecture", label: "Architecture" },
];

export default function NavTabs() {
  const pathname = usePathname();

  return (
    <nav className="hidden items-center gap-1 rounded-full border border-uhc-blue-soft bg-uhc-blue-soft/40 p-0.5 sm:flex">
      {TABS.map((tab) => {
        const active = tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`rounded-full px-3.5 py-1 text-[13px] font-semibold transition-colors ${
              active
                ? "bg-uhc-blue text-white shadow-sm"
                : "text-uhc-blue hover:bg-white hover:text-uhc-blue-bright"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
