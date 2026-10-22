"use client";

import type { Memo } from "@/lib/types";

export function Results({ memo }: { memo: Memo }) {
  return <p>{memo.summary}</p>;
}
