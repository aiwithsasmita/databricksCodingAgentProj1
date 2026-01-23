# UHC vs Cigna Ambulance Policy Gap Analysis

**UHC Policy:** 2026R0123A  
**UHC Source:** [https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Ambulance-Policy.pdf](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Ambulance-Policy.pdf)

**Cigna Policy:** R18 (Updated 08/29/2025)  
**Cigna Source:** [https://static.cigna.com/assets/chcp/secure/pdf/resourceLibrary/clinReimPolsModifiers/R18_Ambulance_Services.pdf](https://static.cigna.com/assets/chcp/secure/pdf/resourceLibrary/clinReimPolsModifiers/R18_Ambulance_Services.pdf)

**Analysis Date:** January 2026

---

## Summary Comparison Table

| # | Rule/Tactic | UHC | Cigna | Recommendation |
|---|-------------|-----|-------|----------------|
| 1 | Non-Emergency H Modifier | Any valid O/D modifier | Requires "H" in origin OR destination | Adopt H-modifier restriction for A0426/A0428 |
| 2 | T-Code Exclusion | Not explicitly addressed | T2001-T2007 explicitly non-reimbursable | Add explicit T-code denial rule |
| 3 | Waiting Time Charges | A0420 in transport code list | Waiting time explicitly non-reimbursable | Consider removing A0420 or adding restrictions |
| 4 | Unloaded Miles | Not explicitly addressed | Explicitly non-reimbursable | Add explicit denial for unloaded mileage |
| 5 | Non-Licensed Transport | Not explicitly addressed | Wheelchair van, taxi, chair car explicitly excluded | Add explicit exclusion list |
| 6 | Deceased Transport | Not explicitly addressed | Explicitly non-reimbursable | Add explicit denial rule |
| 7 | Ancillary Fees | Not explicitly addressed | Parking, tolls, meals, lodging explicitly denied | Add explicit exclusion |
| 8 | Bundled Codes List | General reference to attachment | 100+ specific codes listed in policy | Embed detailed code list in policy |

---

## 1. Non-Emergency Hospital Requirement

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *"UnitedHealthcare will reimburse a code on the Ambulance Transportation Codes list only when reported with a two-digit ambulance modifier."* | *"Any non-emergent licensed ambulance transport that does not identify either the origin or destination of the transport with an H modifier is not reimbursable."* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna denies non-emergency transports without hospital involvement |
| **Exploitation Risk** | Routine facility transports (R→N, N→P, E→J) billed as ambulance |
| **Suggested Action** | Add H-modifier requirement for non-emergency codes |

**Suggested Policy Language**

> **Non-Emergency Ambulance Transport Limitation**
> 
> For non-emergency ground ambulance services (A0426, A0428), UnitedHealthcare requires that either the origin or destination of the transport be a hospital, identified by the "H" modifier. Non-emergency ambulance transports without "H" in the modifier combination will be denied.

**Denial Code:** `AMB-NONEMERG-H`

---

## 2. T-Code Exclusion

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *Not explicitly addressed in policy* | *"Cigna does not provide separate reimbursement for the following HCPCS T status codes: T2001, T2002, T2003, T2004, T2005 and T2007 with or without the use of the origin/destination modifiers."* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna explicitly denies T-codes for non-emergency transport |
| **Exploitation Risk** | T-codes may be billed for non-covered transport services |
| **Suggested Action** | Add explicit T-code denial list |

**Suggested Policy Language**

> **Non-Reimbursable Transport T-Codes**
> 
> UnitedHealthcare does not provide separate reimbursement for HCPCS T status codes T2001, T2002, T2003, T2004, T2005, and T2007 with or without origin/destination modifiers. These codes represent non-emergency transportation services not covered under ambulance benefits.

**Denial Code:** `AMB-TCODE`

**Codes to Deny:**
| Code | Description |
|------|-------------|
| T2001 | Non-emergency transportation; patient attendant/escort |
| T2002 | Non-emergency transportation; per diem |
| T2003 | Non-emergency transportation; encounter/trip |
| T2004 | Non-emergency transportation; commercial carrier, multi-pass |
| T2005 | Non-emergency transportation; stretcher van |
| T2007 | Transportation waiting time, air ambulance and non-emergency vehicle |

---

## 3. Waiting Time Charges

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *A0420 listed in Ambulance Transportation Codes table: "Ambulance waiting time (ALS/BLS) per half hour"* | *"Cigna does not provide reimbursement for: Waiting time charges (i.e., time spent waiting for the individual)"* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna explicitly excludes waiting time from reimbursement |
| **Exploitation Risk** | Providers may bill excessive waiting time units (A0420) |
| **Suggested Action** | Add waiting time exclusion or unit limits |

**Suggested Policy Language**

> **Ambulance Waiting Time**
> 
> UnitedHealthcare does not provide separate reimbursement for ambulance waiting time (A0420). Time spent waiting for the patient is considered part of the ambulance service and is not separately billable.

**Denial Code:** `AMB-WAIT`

---

## 4. Unloaded Miles

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *Not explicitly addressed* | *"Cigna does not provide reimbursement for: Charges for unloaded miles (i.e., miles traveled without the individual on board)"* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna explicitly denies mileage without patient on board |
| **Exploitation Risk** | Providers may bill mileage for return trips or pre-pickup travel |
| **Suggested Action** | Add explicit unloaded miles denial |

**Suggested Policy Language**

> **Unloaded Mileage**
> 
> UnitedHealthcare does not provide reimbursement for unloaded miles (miles traveled without the patient on board). Only loaded mileage from point of pickup to destination is reimbursable.

**Denial Code:** `AMB-UNLOAD`

---

## 5. Non-Licensed Transport Exclusion

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *"UnitedHealthcare considers only an Ambulance Supplier as eligible for reimbursement"* (general statement) | *"Cigna does not provide reimbursement for: Transportation from a non-licensed ambulance which include but are not limited to wheelchair van, chair car, taxi, automobile, private or commercial air travel, bus and mini-bus service"* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna explicitly lists excluded non-ambulance transport types |
| **Exploitation Risk** | Non-ambulance services billed under ambulance codes |
| **Suggested Action** | Add explicit exclusion list for non-licensed transport |

**Suggested Policy Language**

> **Non-Licensed Transport Exclusion**
> 
> UnitedHealthcare does not provide reimbursement for transportation services from non-licensed ambulance providers, including but not limited to: wheelchair van, chair car, taxi, automobile, private vehicle, commercial air travel, bus, and mini-bus services. These services are not eligible under ambulance benefits regardless of codes billed.

**Denial Code:** `AMB-NONLIC`

---

## 6. Deceased Transport

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *Not explicitly addressed* | *"Cigna does not provide reimbursement for: Services for transfer of a deceased member to a funeral home, morgue or hospital when the individual was pronounced dead at the scene"* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna explicitly denies transport of deceased patients |
| **Exploitation Risk** | Ambulance billed for body transport post-death |
| **Suggested Action** | Add explicit deceased transport denial |

**Suggested Policy Language**

> **Deceased Patient Transport**
> 
> UnitedHealthcare does not provide reimbursement for ambulance services involving transport of a deceased member to a funeral home, morgue, or hospital when the individual was pronounced dead at the scene. Ambulance services are for transport of living patients requiring medical care.

**Denial Code:** `AMB-DECEASED`

---

## 7. Ancillary Fees

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *Not explicitly addressed* | *"Cigna does not provide reimbursement for: Ancillary transportation fees (e.g., parking fees, tolls, meals and lodging)"* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna explicitly excludes ancillary fees |
| **Exploitation Risk** | Providers may bill additional fees beyond transport |
| **Suggested Action** | Add explicit ancillary fee exclusion |

**Suggested Policy Language**

> **Ancillary Transportation Fees**
> 
> UnitedHealthcare does not provide separate reimbursement for ancillary transportation fees including but not limited to: parking fees, tolls, meals, lodging, and other incidental expenses. These are not covered under ambulance benefits.

**Denial Code:** `AMB-ANCIL`

---

## 8. Bundled Codes Explicit List

**Source Text Comparison**

| UHC (2026R0123A) | Cigna (R18) |
|------------------|-------------|
| *"Refer to Attachments section: Ambulance Bundle Codes"* (external reference) | *Policy contains 100+ specific bundled codes inline including: J0131, J0171, J0282, J0461, J1170, J1200, J1610, J1885, J2001, J2060, J2250, J2270, J2300, J2310, J2405, J2550, J2930, J3010, J3475, J7030, J7040, J7120, E0443, E0444, E0445, 93000-93010, A4xxx supplies, etc.* |

**Recommendation**

| Item | Details |
|------|---------|
| **Peer Practice** | Cigna embeds complete bundled code list directly in policy |
| **Exploitation Risk** | External attachment may not be consistently applied |
| **Suggested Action** | Embed full bundled code list in policy body |

**Suggested Policy Language**

> **Services Bundled in Ambulance Transport**
> 
> The following codes are included in ambulance base rate and are not separately reimbursable when billed with ambulance transport codes:

**Bundled Drug Codes (Sample):**
| Code | Description |
|------|-------------|
| J0131 | Acetaminophen injection |
| J0171 | Epinephrine injection |
| J0282 | Amiodarone injection |
| J0461 | Atropine sulfate injection |
| J1170 | Hydromorphone injection |
| J1200 | Diphenhydramine injection |
| J1610 | Glucagon injection |
| J1885 | Ketorolac injection |
| J2001 | Lidocaine injection |
| J2060 | Lorazepam injection |
| J2270 | Morphine sulfate injection |
| J2310 | Naloxone injection |
| J2405 | Ondansetron injection |
| J3010 | Fentanyl injection |
| J7030 | Normal saline 1000cc |
| J7040 | Normal saline 500ml |
| J7120 | Lactated ringers |

**Bundled Supply/Equipment Codes (Sample):**
| Code | Description |
|------|-------------|
| A4611-A4627 | Oxygen supplies |
| A6000-A6550 | Dressings/supplies |
| A7000-A7527 | Respiratory supplies |
| E0424-E0480 | Oxygen equipment |
| E0445 | Oximeter |
| 93000-93010 | EKG services |

**Denial Code:** `AMB-BUND`

---

## Implementation Summary

| Priority | Rule | Denial Code | Action |
|----------|------|-------------|--------|
| HIGH | Non-Emergency H Modifier | AMB-NONEMERG-H | Add modifier edit for A0426/A0428 |
| HIGH | T-Code Exclusion | AMB-TCODE | Add code-level denial |
| MEDIUM | Waiting Time | AMB-WAIT | Deny A0420 or add limits |
| MEDIUM | Unloaded Miles | AMB-UNLOAD | Add mileage validation |
| MEDIUM | Non-Licensed Transport | AMB-NONLIC | Add provider type validation |
| LOW | Deceased Transport | AMB-DECEASED | Add claim-level edit |
| LOW | Ancillary Fees | AMB-ANCIL | Add code-level denial |
| LOW | Bundled Codes | AMB-BUND | Embed list in policy |

---

**Sources:**
- [UHC Ambulance Policy 2026R0123A](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Ambulance-Policy.pdf)
- [Cigna Ambulance Services R18](https://static.cigna.com/assets/chcp/secure/pdf/resourceLibrary/clinReimPolsModifiers/R18_Ambulance_Services.pdf)
