"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Article, DailyDigest, IncomingDailyDigest, Lang } from "@/types";
import { detectLang, t } from "@/i18n";
import Header from "@/components/Header";
import CategoryFilter from "@/components/CategoryFilter";
import NewsCard from "@/components/NewsCard";

function normalizeArticle(article: Partial<Article>): Article {
  return {
    title: article.title ?? "",
    url: article.url ?? "",
    source: article.source ?? "",
    published_at: article.published_at ?? null,
    category: article.category ?? "Data Engineering",
    relevance_score: article.relevance_score ?? 0.5,
    summary_en: article.summary_en ?? "",
    summary_es: article.summary_es ?? "",
    tags: Array.isArray(article.tags)
      ? article.tags.filter((tag): tag is string => typeof tag === "string")
      : [],
  };
}

function normalizeDigest(data: IncomingDailyDigest): DailyDigest {
  const articles = Array.isArray(data.articles)
    ? data.articles.map(normalizeArticle)
    : [];

  return {
    date: data.date,
    generated_at: data.generated_at,
    total_sources_checked:
      data.total_sources_checked ??
      new Set(articles.map((a) => a.source).filter(Boolean)).size,
    total_raw_collected:
      data.total_raw_collected ??
      data.total_articles_collected ??
      articles.length,
    total_published: data.total_published ?? articles.length,
    articles,
  };
}

/* Loading skeleton! */

function SkeletonCard({ featured = false }: { featured?: boolean }) {
  return (
    <div
      className={`rounded-2xl border border-white/[0.04] ${featured ? "p-6 sm:p-8" : "p-5"}`}
    >
      {featured && <div className="skeleton h-5 w-20 mb-4 rounded-full" />}
      <div className="flex gap-2 mb-3">
        <div className="skeleton h-4 w-24" />
        <div className="skeleton h-4 w-10" />
      </div>
      <div className="skeleton h-6 w-3/4 mb-2" />
      {featured && <div className="skeleton h-6 w-1/2 mb-3" />}
      <div className="skeleton h-4 w-full mb-1" />
      <div className="skeleton h-4 w-2/3" />
      <div className="flex gap-2 mt-4">
        <div className="skeleton h-5 w-14 rounded-full" />
        <div className="skeleton h-5 w-14 rounded-full" />
      </div>
    </div>
  );
}

function SkeletonPage() {
  return (
    <div className="min-h-screen bg-[#050507]">
      <div className="relative overflow-hidden">
        <div className="orb w-[500px] h-[500px] bg-indigo-600 -top-48 -left-24" />
        <div
          className="orb w-[400px] h-[400px] bg-violet-600 -top-32 right-0"
          style={{ animationDelay: "-7s" }}
        />
        <div className="mx-auto max-w-6xl px-5 pt-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="skeleton h-8 w-8 rounded-xl" />
              <div className="skeleton h-4 w-20" />
            </div>
            <div className="skeleton h-7 w-16 rounded-full" />
          </div>
        </div>
        <div className="mx-auto max-w-6xl px-5 pt-16 pb-12">
          <div className="skeleton h-4 w-28 mb-3" />
          <div className="skeleton h-12 w-64 mb-3" />
          <div className="skeleton h-5 w-80" />
          <div className="flex gap-8 mt-8">
            {[1, 2, 3].map((i) => (
              <div key={i}>
                <div className="skeleton h-8 w-12 mb-1" />
                <div className="skeleton h-3 w-20" />
              </div>
            ))}
          </div>
        </div>
        <div className="gradient-line" />
      </div>
      <main className="mx-auto max-w-6xl px-5 pb-16 pt-8">
        <div className="skeleton h-12 w-full max-w-2xl mb-8 rounded-2xl" />
        <SkeletonCard featured />
        <div className="grid gap-4 sm:grid-cols-2 mt-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </main>
    </div>
  );
}

/* Icons for empty category states */

const CATEGORY_ICONS: Record<string, string> = {
  All: "\u{1F4CA}",
  AWS: "\u2601\uFE0F",
  "Data Engineering": "\u{1F527}",
  Analytics: "\u{1F4C8}",
  "ML/AI": "\u{1F9E0}",
  "Open Source Tools": "\u{1F513}",
  "Case Studies": "\u{1F4DA}",
};

/* Main page starts here */

export default function Home() {
  const [digest, setDigest] = useState<DailyDigest | null>(null);
  const [lang, setLang] = useState<Lang>(() => detectLang());
  const [activeCategory, setActiveCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [currentDateIdx, setCurrentDateIdx] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const apiBase = process.env.NEXT_PUBLIC_API_URL?.trim() || "";

  /* First load! Get digest and dates at the same time */
  useEffect(() => {
    Promise.all([
      fetch(`${apiBase}/api/digests/latest`).then((r) =>
        r.ok ? (r.json() as Promise<IncomingDailyDigest>) : null,
      ),
      fetch(`${apiBase}/api/digests/dates`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
    ])
      .then(([digestData, indexData]) => {
        if (digestData) setDigest(normalizeDigest(digestData));
        if (indexData) {
          const dates = indexData.dates || indexData;
          if (Array.isArray(dates)) setAvailableDates(dates);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [apiBase]);

  /* Show the scroll button when the page is long */
  useEffect(() => {
    const onScroll = () => setShowScrollTop(window.scrollY > 400);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  /* Move between days here */
  const navigateDay = useCallback(
    (direction: "prev" | "next") => {
      const newIdx =
        direction === "prev" ? currentDateIdx + 1 : currentDateIdx - 1;
      if (newIdx < 0 || newIdx >= availableDates.length) return;
      setCurrentDateIdx(newIdx);
      setLoading(true);
      setActiveCategory("All");
      fetch(`${apiBase}/api/digests/${availableDates[newIdx]}`)
        .then((r) =>
          r.ok ? (r.json() as Promise<IncomingDailyDigest>) : null,
        )
        .then((data) => {
          if (data) setDigest(normalizeDigest(data));
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    },
    [apiBase, currentDateIdx, availableDates],
  );

  const categoryCounts = useMemo(() => {
    if (!digest) return {};
    const counts: Record<string, number> = {};
    for (const article of digest.articles) {
      counts[article.category] = (counts[article.category] || 0) + 1;
    }
    return counts;
  }, [digest]);

  const filteredArticles = useMemo(() => {
    if (!digest) return [];
    if (activeCategory === "All") return digest.articles;
    return digest.articles.filter((a) => a.category === activeCategory);
  }, [digest, activeCategory]);

  /* Still loading! */
  if (loading) return <SkeletonPage />;

  /* No digest yet */
  if (!digest) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#050507] gap-3">
        <div className="h-12 w-12 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
          <span className="text-white/20 text-xl">?</span>
        </div>
        <p className="text-white/30 text-sm">No data available yet</p>
        <p className="text-white/15 text-xs">
          Run the pipeline to generate your first digest
        </p>
      </div>
    );
  }

  const [featured, ...rest] = filteredArticles;

  return (
    <div className="min-h-screen bg-[#050507] relative">
      {/* Soft dot grid in the back */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.035) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative">
        <Header
          lang={lang}
          onToggleLang={() => setLang((l) => (l === "en" ? "es" : "en"))}
          date={digest.date}
          generatedAt={digest.generated_at}
          stats={{
            sources: digest.total_sources_checked,
            raw: digest.total_raw_collected,
            published: digest.total_published,
          }}
          onPrevDay={() => navigateDay("prev")}
          onNextDay={() => navigateDay("next")}
          hasPrevDay={currentDateIdx < availableDates.length - 1}
          hasNextDay={currentDateIdx > 0}
        />

        <main className="mx-auto max-w-6xl px-5 pb-16 pt-8">
          {/* Category filter */}
          <div className="mb-8">
            <CategoryFilter
              lang={lang}
              active={activeCategory}
              counts={categoryCounts}
              onChange={setActiveCategory}
            />
          </div>

          {/* Key helps restart the card animation when the category changes */}
          <div key={activeCategory} className="animate-fade-up">
            {filteredArticles.length === 0 ? (
              <div className="py-24 text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-white/[0.03] border border-white/[0.06] mb-4">
                  <span className="text-2xl">
                    {CATEGORY_ICONS[activeCategory] || "\u{1F4CA}"}
                  </span>
                </div>
                <p className="text-white/30 text-sm">
                  {t(lang, "no_articles")}
                </p>
              </div>
            ) : (
              <>
                {featured && (
                  <div className="mb-4">
                    <NewsCard article={featured} lang={lang} featured />
                  </div>
                )}

                {rest.length > 0 && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {rest.map((article, i) => (
                      <div
                        key={article.url}
                        className="animate-fade-up"
                        style={{ animationDelay: `${(i + 1) * 50}ms` }}
                      >
                        <NewsCard article={article} lang={lang} />
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/[0.04] py-8">
          <div className="mx-auto max-w-6xl px-5 flex flex-col sm:flex-row items-center justify-between gap-4 text-[13px] text-white/20">
            <span>{t(lang, "powered_by")}</span>
            <div className="flex items-center gap-3">
              <span>{t(lang, "built_with")}</span>
              <span className="text-white/10">&middot;</span>
              <span>Cocolake &copy; {new Date().getFullYear()}</span>
            </div>
          </div>
        </footer>
      </div>

      {/* Scroll back to the top */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className={`fixed bottom-6 right-6 z-50 glass rounded-full w-10 h-10 flex items-center justify-center border border-white/[0.06] text-white/40 hover:text-white/80 transition-all duration-300 hover:border-white/10 shadow-lg ${
          showScrollTop
            ? "opacity-100 translate-y-0"
            : "opacity-0 translate-y-4 pointer-events-none"
        }`}
        aria-label="Scroll to top"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M8 12V4M4 7l4-4 4 4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  );
}
