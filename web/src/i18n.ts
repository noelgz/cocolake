import { Lang } from "./types";

const translations: Record<Lang, Record<string, string>> = {
  en: {
    title: "Cocolake",
    subtitle: "What happened in data today",
    filter_all: "All",
    sources_checked: "sources checked",
    articles_curated: "articles curated",
    published: "published",
    no_articles: "No articles found for this category.",
    powered_by: "Curated from RSS feeds, Hacker News, Dev.to & GitHub Trending",
    read_more: "Read more",
    updated: "Last updated",
    top_story: "Top Story",
    built_with: "Built with Agentic AI",
    category_AWS: "AWS",
    category_Data_Engineering: "Data Engineering",
    category_Analytics: "Analytics",
    category_ML_AI: "ML/AI",
    category_Open_Source_Tools: "Open Source",
    category_Case_Studies: "Case Studies",
  },
  es: {
    title: "Cocolake",
    subtitle: "Qué pasó hoy en el mundo data",
    filter_all: "Todas",
    sources_checked: "fuentes consultadas",
    articles_curated: "artículos curados",
    published: "publicados",
    no_articles: "No se encontraron artículos para esta categoría.",
    powered_by: "Curado desde RSS feeds, Hacker News, Dev.to y GitHub Trending",
    read_more: "Leer más",
    updated: "Última actualización",
    top_story: "Destacado",
    built_with: "Construido con IA Agéntica",
    category_AWS: "AWS",
    category_Data_Engineering: "Data Engineering",
    category_Analytics: "Analytics",
    category_ML_AI: "ML/AI",
    category_Open_Source_Tools: "Open Source",
    category_Case_Studies: "Casos de Estudio",
  },
};

export function detectLang(): Lang {
  if (typeof navigator === "undefined") return "en";
  const browserLang = navigator.language || "";
  if (browserLang.startsWith("es")) return "es";
  return "en";
}

export function t(lang: Lang, key: string): string {
  return translations[lang]?.[key] ?? translations.en[key] ?? key;
}

export function getCategoryKey(category: string): string {
  return `category_${category.replace(/[\s/]/g, "_")}`;
}
