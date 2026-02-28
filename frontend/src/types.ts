export type Person = { family?: string; given?: string; literal?: string };
export type Item = {
  id: string;
  inputKey: string;
  type: string;
  title: string;
  authors: Person[];
  issued?: string;
  accessed?: string;
  url?: string;
  doi?: string;
  publisher?: string;
  containerTitle?: string;
  tags: string[];
};
export type Proposal = {
  id: string;
  itemId: string;
  stepId: string;
  patch: { op: string; path: string; value?: string }[];
  rationale: string;
  provenance: { source: string; retrievedAt: string; confidence: number };
};
