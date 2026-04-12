import { Hospital } from "./types";

export interface SimilarProvider {
  hospital: Hospital;
  score: number;
  reasons: string[];
}

function normalize(val: number, min: number, max: number): number {
  if (max === min) return 0;
  return (val - min) / (max - min);
}

export function findSimilarProviders(
  target: Hospital,
  all: Hospital[],
  topN = 10
): SimilarProvider[] {
  const others = all.filter((h) => h.npi !== target.npi);

  const payments = all.map((h) => h.totalPayment);
  const beds = all.map((h) => h.bedCount);
  const claims = all.map((h) => h.claimCount);
  const efficiencies = all.map((h) => h.billingEfficiency);

  const payMin = Math.min(...payments), payMax = Math.max(...payments);
  const bedMin = Math.min(...beds), bedMax = Math.max(...beds);
  const clmMin = Math.min(...claims), clmMax = Math.max(...claims);
  const effMin = Math.min(...efficiencies), effMax = Math.max(...efficiencies);

  const tPay = normalize(target.totalPayment, payMin, payMax);
  const tBed = normalize(target.bedCount, bedMin, bedMax);
  const tClm = normalize(target.claimCount, clmMin, clmMax);
  const tEff = normalize(target.billingEfficiency, effMin, effMax);

  const scored = others.map((h) => {
    const reasons: string[] = [];
    let score = 0;

    if (h.orgType === target.orgType) {
      score += 25;
      reasons.push("Same org type");
    }
    if (h.specialty === target.specialty) {
      score += 20;
      reasons.push("Same specialty");
    }
    if (h.billingPattern === target.billingPattern) {
      score += 15;
      reasons.push("Same billing pattern");
    }
    if (h.serviceAddress.state === target.serviceAddress.state) {
      score += 10;
      reasons.push("Same state");
    }

    const payDiff = Math.abs(normalize(h.totalPayment, payMin, payMax) - tPay);
    score += (1 - payDiff) * 10;

    const bedDiff = Math.abs(normalize(h.bedCount, bedMin, bedMax) - tBed);
    score += (1 - bedDiff) * 8;

    const clmDiff = Math.abs(normalize(h.claimCount, clmMin, clmMax) - tClm);
    score += (1 - clmDiff) * 7;

    const effDiff = Math.abs(normalize(h.billingEfficiency, effMin, effMax) - tEff);
    score += (1 - effDiff) * 5;

    if (payDiff < 0.15) reasons.push("Similar payment");
    if (bedDiff < 0.15) reasons.push("Similar bed count");
    if (effDiff < 0.1) reasons.push("Similar efficiency");

    return { hospital: h, score: Math.round(score), reasons };
  });

  return scored.sort((a, b) => b.score - a.score).slice(0, topN);
}
