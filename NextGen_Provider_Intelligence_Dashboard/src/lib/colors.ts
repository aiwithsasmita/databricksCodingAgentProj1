import { OrgType } from "./types";

export const ORG_TYPE_COLORS: Record<OrgType, [number, number, number]> = {
  Hospital: [41, 98, 255],
  "Nursing Home": [255, 56, 96],
  Clinic: [0, 184, 148],
  "Rehab Center": [142, 68, 223],
};

export const ORG_TYPE_HEX: Record<OrgType, string> = {
  Hospital: "#2962FF",
  "Nursing Home": "#FF3860",
  Clinic: "#00B894",
  "Rehab Center": "#8E44DF",
};
