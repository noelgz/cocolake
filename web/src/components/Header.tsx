"use client";

import { useEffect, useState } from "react";
import { Lang } from "@/types";
import { t } from "@/i18n";

interface HeaderProps {
  lang: Lang;
  onToggleLang: () => void;
  date: string;
  generatedAt?: string;
  stats: {
    sources: number;
    raw: number;
    published: number;
  };
  onPrevDay?: () => void;
  onNextDay?: () => void;
  hasPrevDay?: boolean;
  hasNextDay?: boolean;
}

function useCountUp(target: number, duration = 800) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (target === 0) {
      setValue(0);
      return;
    }
    let raf: number;
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(eased * target));
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

function useTimeAgo(isoDate: string | undefined, lang: Lang) {
  const [text, setText] = useState("");
  useEffect(() => {
    if (!isoDate) return;
    const update = () => {
      const diff = Date.now() - new Date(isoDate).getTime();
      const mins = Math.floor(diff / 60000);
      if (mins < 1) {
        setText(lang === "es" ? "ahora" : "just now");
      } else if (mins < 60) {
        setText(lang === "es" ? `hace ${mins}m` : `${mins}m ago`);
      } else {
        const hours = Math.floor(mins / 60);
        setText(lang === "es" ? `hace ${hours}h` : `${hours}h ago`);
      }
    };
    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [isoDate, lang]);
  return text;
}

export default function Header({
  lang,
  onToggleLang,
  date,
  generatedAt,
  stats,
  onPrevDay,
  onNextDay,
  hasPrevDay = false,
  hasNextDay = false,
}: HeaderProps) {
  const sources = useCountUp(stats.sources);
  const raw = useCountUp(stats.raw);
  const published = useCountUp(stats.published);
  const updatedAgo = useTimeAgo(generatedAt, lang);

  return (
    <div className="relative overflow-hidden">
      {/* Floating gradient orbs! */}
      <div className="orb w-[500px] h-[500px] bg-indigo-600 -top-48 -left-24" />
      <div
        className="orb w-[400px] h-[400px] bg-violet-600 -top-32 right-0"
        style={{ animationDelay: "-7s" }}
      />
      <div
        className="orb w-[300px] h-[300px] bg-fuchsia-600 top-20 left-1/3"
        style={{ animationDelay: "-13s" }}
      />

      {/* Top nav */}
      <nav className="relative z-10 mx-auto max-w-6xl px-5 pt-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <svg
                width="20"
                height="20"
                viewBox="0 0 28 28"
                fill="none"
              >
                {/* Croc eyes over the water! */}
                <circle cx="9.5" cy="9" r="3" fill="white" fillOpacity={0.9} />
                <circle cx="18.5" cy="9" r="3" fill="white" fillOpacity={0.9} />
                {/* Thin pupils */}
                <ellipse cx="9.5" cy="9" rx="0.7" ry="2" fill="black" fillOpacity={0.2} />
                <ellipse cx="18.5" cy="9" rx="0.7" ry="2" fill="black" fillOpacity={0.2} />
                {/* Water line */}
                <path
                  d="M3 17c3.5-2.5 6-2.5 10 0s6.5 2.5 10 0"
                  stroke="white"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  opacity="0.7"
                />
                {/* Small ripple */}
                <path
                  d="M5 22c3-2 5-2 8 0s5 2 8 0"
                  stroke="white"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                  opacity="0.35"
                />
              </svg>
            </div>
            <span className="text-sm font-semibold text-white/90">
              Cocolake
            </span>
          </div>

          <button
            onClick={onToggleLang}
            className="glass rounded-full px-3 py-1.5 text-xs font-medium text-white/50 border border-white/[0.06] transition hover:text-white/80 hover:border-white/10"
          >
            {lang === "en" ? "Espa\u00f1ol" : "English"}
          </button>
        </div>
      </nav>

      {/* Hero area */}
      <header className="relative z-10 mx-auto max-w-6xl px-5 pt-16 pb-12">
        {/* Date, day arrows, and live update text */}
        <div className="flex items-center gap-3 mb-3">
          <div className="flex items-center gap-2">
            {hasPrevDay && (
              <button
                onClick={onPrevDay}
                className="text-white/20 hover:text-white/60 transition text-sm"
                aria-label="Previous day"
              >
                &larr;
              </button>
            )}
            <p className="text-sm font-medium text-indigo-400">{date}</p>
            {hasNextDay && (
              <button
                onClick={onNextDay}
                className="text-white/20 hover:text-white/60 transition text-sm"
                aria-label="Next day"
              >
                &rarr;
              </button>
            )}
          </div>
          {updatedAgo && (
            <div className="flex items-center gap-1.5 text-[12px] text-white/25">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot" />
              <span>
                {lang === "es" ? "Actualizado" : "Updated"} {updatedAgo}
              </span>
            </div>
          )}
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1] gradient-text">
          {t(lang, "title")}
        </h1>
        <p className="mt-3 max-w-lg text-base text-white/40 leading-relaxed">
          {t(lang, "subtitle")}
        </p>

        {/* Stats with a small count-up effect */}
        <div className="mt-8 flex gap-8">
          {[
            { value: sources, label: t(lang, "sources_checked") },
            { value: raw, label: t(lang, "articles_curated") },
            { value: published, label: t(lang, "published") },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="text-2xl font-semibold text-white tabular-nums">
                {stat.value}
              </p>
              <p className="text-xs text-white/30 mt-0.5">{stat.label}</p>
            </div>
          ))}
        </div>
      </header>

      {/* Gradient line at the bottom */}
      <div className="gradient-line" />
    </div>
  );
}
