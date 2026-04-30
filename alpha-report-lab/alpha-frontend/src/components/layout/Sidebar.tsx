"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FileText, PlusCircle } from "lucide-react";
import { cls } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/generate", label: "Generate Report", icon: PlusCircle },
  { href: "/reports", label: "Report History", icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-60 shrink-0 border-r border-gray-800 bg-gray-950/60 flex flex-col">
      <div className="px-5 py-6 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-alpha-green to-alpha-blue flex items-center justify-center text-white font-bold">
            α
          </div>
          <div>
            <div className="font-semibold tracking-tight">Alpha Report Lab</div>
            <div className="text-xs text-gray-500">AI Research</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {NAV.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cls(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition",
                active
                  ? "bg-alpha-blue/20 text-alpha-blue border border-alpha-blue/30"
                  : "text-gray-400 hover:text-gray-100 hover:bg-gray-900"
              )}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-3 text-xs text-gray-600 border-t border-gray-800">
        Dynatrace Instrumentation Demo
      </div>
    </aside>
  );
}
