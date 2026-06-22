export interface SourceCitation {
  title: string;
  url: string;
  score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  sources?: SourceCitation[];
}

export interface PageInfo {
  url: string;
  title: string;
  content: string;
}

export interface IngestResponse {
  status: string;
  chunks_stored: number;
  url: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
}
