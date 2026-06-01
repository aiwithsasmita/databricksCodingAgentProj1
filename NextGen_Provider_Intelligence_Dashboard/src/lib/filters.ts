import { Hospital, Filters } from "./types";

export const ALL = "All";

export function applyFilters(data: Hospital[], filters: Filters): Hospital[] {
  return data.filter((h) => {
    if (filters.specialty !== ALL && h.specialty !== filters.specialty) return false;
    if (filters.billingPattern !== ALL && h.billingPattern !== filters.billingPattern) return false;
    if (filters.serviceState !== ALL && h.serviceAddress.state !== filters.serviceState) return false;
    if (filters.orgType !== ALL && h.orgType !== filters.orgType) return false;
    return true;
  });
}

export function getUniqueValues<K extends keyof Hospital>(
  data: Hospital[],
  key: K
): string[] {
  const set = new Set<string>();
  data.forEach((h) => {
    const val = h[key];
    if (typeof val === "string") set.add(val);
  });
  return Array.from(set).sort();
}

export function getUniqueStates(data: Hospital[], field: "serviceAddress" | "billingAddress"): string[] {
  const set = new Set<string>();
  data.forEach((h) => set.add(h[field].state));
  return Array.from(set).sort();
}
