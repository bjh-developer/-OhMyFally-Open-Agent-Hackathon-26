import index from "./ago-index.json";

export interface AgoChunk {
  report: string;
  fy: string;
  section: string;
  page: string;
  url: string;
  text: string;
}

// Static snapshot of data/ago/ (verbatim AGO excerpts), keyed by chunk_id, which is what Finding.ago_refs holds.
export function agoChunk(id: string): AgoChunk | undefined {
  return (index as Record<string, AgoChunk>)[id];
}
