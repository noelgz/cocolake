"use client";

import { Article, Lang } from "@/types";
import { getCategoryKey, t } from "@/i18n";

interface NewsCardProps {
  article: Article;
  lang: Lang;
  featured?: boolean;
}

const CATEGORY_GRADIENT: Record<string, string> = {
  AWS: "from-amber-500/10 to-orange-500/5",
  "Data Engineering": "from-blue-500/10 to-cyan-500/5",
  Analytics: "from-violet-500/10 to-purple-500/5",
  "ML/AI": "from-rose-500/10 to-pink-500/5",
  "Open Source Tools": "from-emerald-500/10 to-teal-500/5",
  "Case Studies": "from-sky-500/10 to-indigo-500/5",
};

const CATEGORY_ACCENT: Record<string, string> = {
  AWS: "text-amber-400",
  "Data Engineering": "text-blue-400",
  Analytics: "text-violet-400",
  "ML/AI": "text-rose-400",
  "Open Source Tools": "text-emerald-400",
  "Case Studies": "text-sky-400",
};

const CATEGORY_TAG: Record<string, string> = {
  AWS: "bg-amber-500/10 text-amber-400/70",
  "Data Engineering": "bg-blue-500/10 text-blue-400/70",
  Analytics: "bg-violet-500/10 text-violet-400/70",
  "ML/AI": "bg-rose-500/10 text-rose-400/70",
  "Open Source Tools": "bg-emerald-500/10 text-emerald-400/70",
  "Case Studies": "bg-sky-500/10 text-sky-400/70",
};

const CATEGORY_GLOW: Record<string, string> = {
  AWS: "rgba(245, 158, 11, 0.12)",
  "Data Engineering": "rgba(59, 130, 246, 0.12)",
  Analytics: "rgba(139, 92, 246, 0.12)",
  "ML/AI": "rgba(244, 63, 94, 0.12)",
  "Open Source Tools": "rgba(16, 185, 129, 0.12)",
  "Case Studies": "rgba(14, 165, 233, 0.12)",
};

const SOURCE_BADGE: Record<string, { bg: string; text: string }> = {
  "hacker news": { bg: "bg-orange-500/15", text: "text-orange-300/80" },
  hackernews: { bg: "bg-orange-500/15", text: "text-orange-300/80" },
  hn: { bg: "bg-orange-500/15", text: "text-orange-300/80" },
  "dev.to": { bg: "bg-indigo-500/15", text: "text-indigo-300/80" },
  devto: { bg: "bg-indigo-500/15", text: "text-indigo-300/80" },
  github: { bg: "bg-white/10", text: "text-white/60" },
};

function getSourceBadge(source: string): { bg: string; text: string } {
  const lower = source.toLowerCase();
  for (const [key, style] of Object.entries(SOURCE_BADGE)) {
    if (lower.includes(key)) return style;
  }
  return { bg: "bg-indigo-500/10", text: "text-indigo-300/60" };
}

function timeAgo(dateStr: string | null, lang: Lang): string {
  if (!dateStr) return "";
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return lang === "es" ? "Ahora" : "Just now";
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
  } catch {
    return "";
  }
}

function sourceName(source: string): string {
  return source.replace("RSS: ", "").replace(/\s*\(.*\)/, "");
}

function RelevanceDots({ score }: { score: number }) {
  const filled = Math.round(score * 5);
  return (
    <div
      className="flex gap-[3px] items-center"
      title={`Relevance: ${Math.round(score * 100)}%`}
    >
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`w-1 h-1 rounded-full transition-colors ${
            i <= filled ? "bg-white/40" : "bg-white/10"
          }`}
        />
      ))}
    </div>
  );
}

export default function NewsCard({
  article,
  lang,
  featured = false,
}: NewsCardProps) {
  const summary = lang === "es" ? article.summary_es : article.summary_en;
  const gradient =
    CATEGORY_GRADIENT[article.category] || "from-zinc-500/10 to-zinc-500/5";
  const accent = CATEGORY_ACCENT[article.category] || "text-zinc-400";
  const tagStyle =
    CATEGORY_TAG[article.category] || "bg-white/[0.05] text-white/30";
  const categoryLabel = t(lang, getCategoryKey(article.category));
  const time = timeAgo(article.published_at, lang);
  const sourceBadge = getSourceBadge(article.source);
  const glowColor =
    CATEGORY_GLOW[article.category] || "rgba(99, 102, 241, 0.08)";

  if (featured) {
    return (
      <article className="group gradient-border-featured rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent p-6 sm:p-8">
        {/* Top story badge and relevance dots! */}
        <div className="flex items-center gap-3 mb-4">
          <span className="inline-flex items-center rounded-full bg-indigo-500/15 px-3 py-1 text-[11px] font-semibold text-indigo-300 uppercase tracking-wide">
            {t(lang, "top_story")}
          </span>
          <RelevanceDots score={article.relevance_score} />
        </div>

        <div className="flex items-center gap-3 text-sm">
          <span className={`font-medium ${accent}`}>{categoryLabel}</span>
          {time && <span className="text-white/20">{time}</span>}
        </div>

        <h3 className="mt-3 text-xl sm:text-2xl font-semibold leading-snug text-white group-hover:text-indigo-200 transition-colors">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="after:absolute after:inset-0"
          >
            {article.title}
          </a>
        </h3>

        <p className="mt-3 text-[15px] leading-relaxed text-white/40 max-w-2xl">
          {summary}
        </p>

        <div className="mt-5 flex items-center justify-between">
          <div className="flex flex-wrap gap-1.5">
            {article.tags.map((tag) => (
              <span
                key={tag}
                className={`rounded-full px-2.5 py-0.5 text-[11px] ${tagStyle}`}
              >
                {tag}
              </span>
            ))}
          </div>
          <span
            className={`inline-flex items-center rounded-full ${sourceBadge.bg} ${sourceBadge.text} px-2.5 py-0.5 text-[10px] font-mono shrink-0 ml-4`}
          >
            {sourceName(article.source)}
          </span>
        </div>
      </article>
    );
  }

  return (
    <article
      className={`group gradient-border rounded-2xl bg-gradient-to-br ${gradient} to-transparent p-5 flex flex-col justify-between h-full`}
      style={{ "--card-glow": glowColor } as React.CSSProperties}
    >
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[13px]">
            <span className={`font-medium ${accent}`}>{categoryLabel}</span>
            {time && <span className="text-white/20">{time}</span>}
          </div>
          <RelevanceDots score={article.relevance_score} />
        </div>

        <h3 className="mt-2.5 text-[15px] font-medium leading-snug text-white/90 group-hover:text-white transition-colors">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="after:absolute after:inset-0"
          >
            {article.title}
          </a>
        </h3>

        <p className="mt-2 text-[13px] leading-relaxed text-white/30 line-clamp-3">
          {summary}
        </p>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex flex-wrap gap-1.5">
          {article.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className={`rounded-full px-2 py-0.5 text-[11px] ${tagStyle}`}
            >
              {tag}
            </span>
          ))}
        </div>
        <span
          className={`inline-flex items-center rounded-full ${sourceBadge.bg} ${sourceBadge.text} px-2 py-0.5 text-[10px] font-mono shrink-0 ml-3`}
        >
          {sourceName(article.source)}
        </span>
      </div>
    </article>
  );
}
