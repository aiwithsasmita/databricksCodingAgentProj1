export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
}

export type OrgType = "Hospital" | "Nursing Home" | "Clinic" | "Rehab Center";
export type Specialty = "Cardiology" | "Orthopedics" | "General" | "Oncology" | "Neurology" | "Pediatrics" | "Pulmonology" | "Gastroenterology";
export type BillingPattern = "High Volume" | "Moderate" | "Low Volume" | "Outlier";
export type BubbleMetric = "totalPayment" | "bedCount";
export type MapMode = "scatter" | "heatmap" | "hexagon";

export interface Hospital {
  npi: string;
  name: string;
  orgType: OrgType;
  specialty: Specialty;
  latitude: number;
  longitude: number;
  serviceAddress: Address;
  billingAddress: Address;
  billingLat: number;
  billingLng: number;
  bedCount: number;
  totalPayment: number;
  billingPattern: BillingPattern;
  billingEfficiency: number;
  claimCount: number;
}

export interface Filters {
  specialty: string;
  billingPattern: string;
  serviceState: string;
  orgType: string;
}
