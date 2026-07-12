export function performLocalSearch(chunks: { id: string; text: string }[], query: string, limit = 3) {
  if (chunks.length === 0) return [];
  const queryLower = query.toLowerCase();
  const queryWords = queryLower.split(/\s+/).filter(w => w.length > 2);
  if (queryWords.length === 0) return chunks.slice(0, limit);

  // --- 1. KEYWORD SEARCH: BM25 / TF-IDF ---
  const totalDocs = chunks.length;
  const docWordFreqs = chunks.map(chunk => {
    const words = chunk.text.toLowerCase().split(/\s+/);
    const counts: Record<string, number> = {};
    words.forEach(w => counts[w] = (counts[w] || 0) + 1);
    return { id: chunk.id, wordCount: words.length, counts };
  });

  // Calculate IDF for each query word
  const idfs: Record<string, number> = {};
  queryWords.forEach(word => {
    const docsWithWord = docWordFreqs.filter(df => df.counts[word] > 0).length;
    idfs[word] = Math.log(1 + (totalDocs - docsWithWord + 0.5) / (docsWithWord + 0.5));
  });

  // Score each chunk with TF-IDF + Exact phrase bonus
  const keywordScored = chunks.map((chunk, index) => {
    const df = docWordFreqs[index];
    let score = 0;
    queryWords.forEach(word => {
      const tf = (df.counts[word] || 0) / df.wordCount;
      const idf = idfs[word] || 0;
      score += tf * idf * 1.5;
    });

    // Exact phrase match bonus
    if (chunk.text.toLowerCase().includes(queryLower)) {
      score += 2.0;
    }
    return { chunk, score };
  });

  // --- 2. SEMANTIC SEARCH: Fuzzy Character Trigram Cosine ---
  const getTrigrams = (str: string): Set<string> => {
    const trigrams = new Set<string>();
    const cleaned = str.toLowerCase().replace(/[^a-z0-9]/g, '');
    for (let i = 0; i < cleaned.length - 2; i++) {
      trigrams.add(cleaned.substring(i, i + 3));
    }
    return trigrams;
  };

  const queryTrigrams = getTrigrams(queryLower);

  const semanticScored = chunks.map(chunk => {
    const chunkTrigrams = getTrigrams(chunk.text);
    if (queryTrigrams.size === 0 || chunkTrigrams.size === 0) return { chunk, score: 0 };

    // Calculate intersection / union (Jaccard / Cosine approximation)
    let intersectionCount = 0;
    queryTrigrams.forEach(tg => {
      if (chunkTrigrams.has(tg)) intersectionCount++;
    });

    const cosineScore = intersectionCount / Math.sqrt(queryTrigrams.size * chunkTrigrams.size);
    return { chunk, score: cosineScore };
  });

  // --- 3. RECIPROCAL RANK FUSION (RRF) ---
  const sortedKeyword = [...keywordScored].sort((a, b) => b.score - a.score);
  const sortedSemantic = [...semanticScored].sort((a, b) => b.score - a.score);

  const keywordRanks: Record<string, number> = {};
  sortedKeyword.forEach((item, index) => {
    keywordRanks[item.chunk.id] = index + 1;
  });

  const semanticRanks: Record<string, number> = {};
  sortedSemantic.forEach((item, index) => {
    semanticRanks[item.chunk.id] = index + 1;
  });

  const rrfScored = chunks.map(chunk => {
    const kRank = keywordRanks[chunk.id] || 9999;
    const sRank = semanticRanks[chunk.id] || 9999;
    const rrfScore = (1 / (60 + kRank)) + (1 / (60 + sRank));
    return { chunk, score: rrfScore };
  });

  return rrfScored
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(item => item.chunk);
}
