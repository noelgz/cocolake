"use client";

import { Lang } from "@/types";
import { getCategoryKey, t } from "@/i18n";

const CATEGORIES = [
  "All",
  "AWS",
  "Data Engineering",
  "Analytics",
  "ML/AI",
  "Open Source Tools",
  "Case Studies",
];

interface CategoryFilterProps {
  lang: Lang;
  active: string;
  counts: Record<string, number>;
  onChange: (category: string) => void;
}

export default function CategoryFilter({
  lang,
  active,
  counts,
  onChange,
}: CategoryFilterProps) {
  return (
    <div className="relative">
      {/* Faded edges on mobile so scroll feels clear */}
      <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-5 bg-gradient-to-r from-[#050507] to-transparent z-10 md:hidden" />
      <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-5 bg-gradient-to-l from-[#050507] to-transparent z-10 md:hidden" />

      <div className="glass rounded-2xl border border-white/[0.06] p-1.5 flex gap-1 overflow-x-auto filter-scroll">
        {CATEGORIES.map((cat) => {
          const isActive = active === cat;
          const label =
            cat === "All"
              ? t(lang, "filter_all")
              : t(lang, getCategoryKey(cat));
          const count = cat === "All" ? undefined : counts[cat] || 0;

          return (
            <button
              key={cat}
              onClick={() => onChange(cat)}
              className={`shrink-0 rounded-xl px-4 py-2 text-[13px] font-medium transition-all duration-200 ${
                isActive
                  ? "bg-white text-zinc-900 shadow-lg shadow-white/10"
                  : "text-white/40 hover:text-white/70"
              }`}
            >
              {label}
              {count !== undefined && count > 0 && (
                <span
                  className={`ml-1.5 text-[11px] ${isActive ? "text-zinc-400" : "text-white/20"}`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
