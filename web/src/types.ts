export interface Article {
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  category: string;
  relevance_score: number;
  summary_en: string;
  summary_es: string;
  tags: string[];
}

export interface DailyDigest {
  date: string;
  generated_at: string;
  total_sources_checked: number;
  total_raw_collected: number;
  total_published: number;
  articles: Article[];
}

export interface IncomingDailyDigest {
  date: string;
  generated_at: string;
  total_sources_checked?: number;
  total_raw_collected?: number;
  total_published?: number;
  total_articles_collected?: number;
  articles: Partial<Article>[];
}

export type Lang = "en" | "es";
