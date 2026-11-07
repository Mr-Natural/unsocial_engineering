// Hand-authored types mirroring the Supabase schema (see supabase/migrations).
// If you later adopt `supabase gen types typescript`, replace the Database type
// below with the generated output and keep the domain aliases at the bottom.

export type ArticleStatus = "draft" | "review" | "flagged" | "published";
export type LeadStatus = "new" | "clustered" | "written" | "discarded";
export type SocialStatus = "pending" | "posted" | "failed";

export interface Database {
  public: {
    Tables: {
      categories: {
        Row: {
          id: string;
          name: string;
          slug: string;
          description: string | null;
          icon: string | null;
        };
        Insert: {
          id?: string;
          name: string;
          slug: string;
          description?: string | null;
          icon?: string | null;
        };
        Update: Partial<Database["public"]["Tables"]["categories"]["Insert"]>;
      };
      leads: {
        Row: {
          id: string;
          source: string;
          title: string | null;
          source_url: string | null;
          raw_text: string | null;
          relevance_score: number | null;
          status: string;
          scraped_at: string;
          cluster_id: string | null;
        };
        Insert: {
          id?: string;
          source: string;
          title?: string | null;
          source_url?: string | null;
          raw_text?: string | null;
          relevance_score?: number | null;
          status?: string;
          scraped_at?: string;
          cluster_id?: string | null;
        };
        Update: Partial<Database["public"]["Tables"]["leads"]["Insert"]>;
      };
      articles: {
        Row: {
          id: string;
          title: string;
          slug: string;
          body_html: string | null;
          summary: string | null;
          category_id: string | null;
          source_urls: string[];
          ai_confidence: number | null;
          status: string;
          editor_notes: string | null;
          revised_at: string | null;
          evidence_label: string | null;
          editorial_stream: string | null;
          region: string | null;
          research_as_of: string | null;
          author_credit: string | null;
          created_at: string;
          published_at: string | null;
        };
        Insert: {
          id?: string;
          title: string;
          slug: string;
          body_html?: string | null;
          summary?: string | null;
          category_id?: string | null;
          source_urls?: string[];
          ai_confidence?: number | null;
          status?: string;
          editor_notes?: string | null;
          revised_at?: string | null;
          evidence_label?: string | null;
          editorial_stream?: string | null;
          region?: string | null;
          research_as_of?: string | null;
          author_credit?: string | null;
          created_at?: string;
          published_at?: string | null;
        };
        Update: Partial<Database["public"]["Tables"]["articles"]["Insert"]>;
      };
      social_posts: {
        Row: {
          id: string;
          article_id: string | null;
          platform: string;
          content: string | null;
          posted_at: string | null;
          status: string;
        };
        Insert: {
          id?: string;
          article_id?: string | null;
          platform: string;
          content?: string | null;
          posted_at?: string | null;
          status?: string;
        };
        Update: Partial<Database["public"]["Tables"]["social_posts"]["Insert"]>;
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
}

// Convenience domain aliases.
export type Category = Database["public"]["Tables"]["categories"]["Row"];
export type Lead = Database["public"]["Tables"]["leads"]["Row"];
export type Article = Database["public"]["Tables"]["articles"]["Row"];
export type SocialPost = Database["public"]["Tables"]["social_posts"]["Row"];
