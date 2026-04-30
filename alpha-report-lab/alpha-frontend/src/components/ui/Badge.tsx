import { cls } from "@/lib/utils";
import { ReactNode } from "react";

export default function Badge({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cls(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-md border",
        className || "bg-gray-800 text-gray-300 border-gray-700"
      )}
    >
      {children}
    </span>
  );
}
