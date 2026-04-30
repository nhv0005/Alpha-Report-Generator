import { cls } from "@/lib/utils";

export default function Skeleton({ className }: { className?: string }) {
  return <div className={cls("rounded-md bg-gray-800 pulse-soft", className)} />;
}
