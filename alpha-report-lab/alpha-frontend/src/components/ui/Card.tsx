import { cls } from "@/lib/utils";
import { ReactNode } from "react";

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cls(
        "rounded-xl border border-gray-800 bg-gray-900/40 p-5",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cls("mb-3", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cls("text-sm font-medium text-gray-400", className)}>{children}</div>;
}

export function CardValue({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cls("text-2xl font-semibold text-gray-100", className)}>{children}</div>;
}
