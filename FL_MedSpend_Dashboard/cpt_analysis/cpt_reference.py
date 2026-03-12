"""
CPT Reference Master — ~200 high-impact CPT/HCPCS codes with RVUs, categories,
and CMS national average allowed amounts (2024 Physician Fee Schedule basis).
"""

import pandas as pd

# ── Service categories ────────────────────────────────────────────────
CATEGORIES = [
    "E&M", "Surgery", "Radiology", "Lab", "Medicine",
    "Anesthesia", "DME/Supply", "Behavioral Health",
]

SUBCATEGORIES = {
    "E&M": ["Office Visit", "Hospital Visit", "ER Visit", "Consultation",
             "Preventive", "Telehealth", "Care Management"],
    "Surgery": ["Orthopedic", "Cardiac", "General", "Neurosurgery",
                "Ophthalmology", "Urology", "Vascular", "Spine"],
    "Radiology": ["Diagnostic X-ray", "CT", "MRI", "Ultrasound",
                  "Nuclear Medicine", "Radiation Therapy", "Mammography"],
    "Lab": ["Chemistry", "Hematology", "Pathology", "Microbiology",
            "Molecular/Genetics"],
    "Medicine": ["Cardiology Dx", "Pulmonary", "Gastroenterology",
                 "Nephrology/Dialysis", "Infusion/Injection", "Physical Therapy",
                 "Ophthalmology Dx", "Allergy/Immunology"],
    "Anesthesia": ["General Anesthesia", "Regional Anesthesia", "Pain Management"],
    "DME/Supply": ["Orthotics", "Prosthetics", "Oxygen/Respiratory", "Diabetic Supply"],
    "Behavioral Health": ["Psychiatry", "Psychotherapy", "Substance Abuse",
                          "Neuropsych Testing"],
}

# ── CPT Master List ───────────────────────────────────────────────────
# Fields: code, description, category, subcategory, rvu_work, rvu_total,
#         national_avg_allowed, annual_utilization_per_1000 (baseline)
CPT_DATA = [
    # ═══ E&M — Office Visits ═══
    ("99202", "Office visit new, low", "E&M", "Office Visit", 0.93, 1.58, 76, 45),
    ("99203", "Office visit new, moderate", "E&M", "Office Visit", 1.60, 2.78, 134, 38),
    ("99204", "Office visit new, mod-high", "E&M", "Office Visit", 2.60, 4.39, 211, 18),
    ("99205", "Office visit new, high", "E&M", "Office Visit", 3.50, 5.82, 280, 6),
    ("99211", "Office visit estab, minimal", "E&M", "Office Visit", 0.18, 0.48, 23, 85),
    ("99212", "Office visit estab, low", "E&M", "Office Visit", 0.70, 1.30, 62, 120),
    ("99213", "Office visit estab, moderate", "E&M", "Office Visit", 1.30, 2.31, 111, 350),
    ("99214", "Office visit estab, mod-high", "E&M", "Office Visit", 1.92, 3.29, 158, 280),
    ("99215", "Office visit estab, high", "E&M", "Office Visit", 2.80, 4.58, 220, 65),
    # ═══ E&M — Hospital ═══
    ("99221", "Initial hospital care, low", "E&M", "Hospital Visit", 1.92, 2.84, 136, 22),
    ("99222", "Initial hospital care, mod", "E&M", "Hospital Visit", 2.61, 3.86, 185, 35),
    ("99223", "Initial hospital care, high", "E&M", "Hospital Visit", 3.86, 5.69, 273, 28),
    ("99231", "Subsequent hospital, low", "E&M", "Hospital Visit", 0.76, 1.12, 54, 55),
    ("99232", "Subsequent hospital, mod", "E&M", "Hospital Visit", 1.39, 2.05, 98, 85),
    ("99233", "Subsequent hospital, high", "E&M", "Hospital Visit", 2.00, 2.95, 142, 40),
    ("99238", "Hospital discharge day", "E&M", "Hospital Visit", 1.28, 1.86, 89, 32),
    ("99239", "Hospital discharge 30+ min", "E&M", "Hospital Visit", 1.90, 2.73, 131, 18),
    # ═══ E&M — ER ═══
    ("99281", "ER visit, minimal", "E&M", "ER Visit", 0.25, 0.69, 33, 15),
    ("99282", "ER visit, low", "E&M", "ER Visit", 0.56, 1.38, 66, 22),
    ("99283", "ER visit, moderate", "E&M", "ER Visit", 1.34, 2.69, 129, 45),
    ("99284", "ER visit, mod-high", "E&M", "ER Visit", 2.56, 4.67, 224, 52),
    ("99285", "ER visit, high severity", "E&M", "ER Visit", 3.80, 6.59, 316, 35),
    ("99291", "Critical care, first hour", "E&M", "ER Visit", 4.50, 7.54, 362, 8),
    # ═══ E&M — Preventive / Telehealth / Care Mgmt ═══
    ("99385", "Preventive visit new 18-39", "E&M", "Preventive", 1.50, 2.70, 130, 25),
    ("99386", "Preventive visit new 40-64", "E&M", "Preventive", 1.75, 3.10, 149, 22),
    ("99395", "Preventive estab 18-39", "E&M", "Preventive", 1.30, 2.42, 116, 40),
    ("99396", "Preventive estab 40-64", "E&M", "Preventive", 1.50, 2.74, 132, 55),
    ("99397", "Preventive estab 65+", "E&M", "Preventive", 1.75, 3.15, 151, 48),
    ("99441", "Telehealth E&M 5-10 min", "E&M", "Telehealth", 0.25, 0.50, 24, 30),
    ("99442", "Telehealth E&M 11-20 min", "E&M", "Telehealth", 0.50, 1.00, 48, 55),
    ("99443", "Telehealth E&M 21-30 min", "E&M", "Telehealth", 0.75, 1.50, 72, 25),
    ("99490", "Chronic care mgmt 20 min", "E&M", "Care Management", 0.61, 1.17, 56, 35),
    ("99491", "Chronic care mgmt 30 min", "E&M", "Care Management", 1.00, 1.82, 87, 18),
    # ═══ Surgery — Orthopedic ═══
    ("27130", "Total hip arthroplasty", "Surgery", "Orthopedic", 20.72, 30.10, 1445, 1.2),
    ("27447", "Total knee arthroplasty", "Surgery", "Orthopedic", 19.72, 28.80, 1382, 1.8),
    ("29881", "Knee arthroscopy, meniscect", "Surgery", "Orthopedic", 4.23, 6.90, 331, 3.5),
    ("29880", "Knee arthroscopy w/ meniscus", "Surgery", "Orthopedic", 5.10, 8.20, 394, 2.8),
    ("23472", "Total shoulder arthroplasty", "Surgery", "Orthopedic", 20.05, 29.50, 1416, 0.6),
    ("27236", "Open treat femoral fracture", "Surgery", "Orthopedic", 13.22, 19.80, 950, 0.8),
    ("22633", "Lumbar arthrodesis combined", "Surgery", "Spine", 27.00, 39.50, 1896, 0.5),
    ("63047", "Lumbar laminectomy", "Surgery", "Spine", 15.37, 22.88, 1098, 0.9),
    ("22551", "Cervical fusion anterior", "Surgery", "Spine", 22.10, 32.40, 1556, 0.7),
    # ═══ Surgery — Cardiac ═══
    ("33533", "CABG single arterial graft", "Surgery", "Cardiac", 33.75, 48.20, 2314, 0.3),
    ("33361", "TAVR percutaneous", "Surgery", "Cardiac", 30.00, 44.50, 2137, 0.2),
    ("92928", "PCI stent single vessel", "Surgery", "Cardiac", 10.13, 15.70, 754, 1.5),
    ("92920", "PCI balloon angioplasty", "Surgery", "Cardiac", 7.50, 11.80, 567, 1.0),
    ("33249", "ICD implant/replace", "Surgery", "Cardiac", 12.00, 18.30, 879, 0.4),
    # ═══ Surgery — General ═══
    ("47562", "Lap cholecystectomy", "Surgery", "General", 7.39, 11.36, 545, 2.5),
    ("44970", "Laparoscopic appendectomy", "Surgery", "General", 7.22, 11.10, 533, 1.8),
    ("49505", "Inguinal hernia repair", "Surgery", "General", 5.39, 8.42, 404, 2.2),
    ("43239", "Upper GI endoscopy w biopsy", "Surgery", "General", 3.14, 5.38, 258, 12),
    ("43249", "Upper GI endoscopy w dilat", "Surgery", "General", 3.55, 5.98, 287, 4),
    ("45380", "Colonoscopy w biopsy", "Surgery", "General", 3.69, 6.13, 294, 18),
    ("45385", "Colonoscopy w polyp removal", "Surgery", "General", 4.57, 7.52, 361, 22),
    ("45378", "Diagnostic colonoscopy", "Surgery", "General", 3.36, 5.58, 268, 35),
    # ═══ Surgery — Ophthalmology ═══
    ("66984", "Cataract removal w IOL", "Surgery", "Ophthalmology", 7.35, 11.67, 560, 8),
    ("67028", "Intravitreal injection", "Surgery", "Ophthalmology", 1.44, 2.48, 119, 15),
    ("65855", "Laser trabeculoplasty", "Surgery", "Ophthalmology", 3.20, 5.10, 245, 2),
    # ═══ Surgery — Urology ═══
    ("52000", "Cystoscopy", "Surgery", "Urology", 2.23, 3.80, 182, 5),
    ("55700", "Prostate biopsy", "Surgery", "Urology", 3.28, 5.40, 259, 3),
    ("52601", "TURP prostatectomy", "Surgery", "Urology", 11.26, 16.90, 811, 0.8),
    # ═══ Surgery — Vascular ═══
    ("36821", "AV fistula creation", "Surgery", "Vascular", 8.37, 12.80, 614, 0.5),
    ("37228", "Lower extremity stent", "Surgery", "Vascular", 9.50, 14.60, 701, 0.6),
    ("36247", "Selective catheter 2nd order", "Surgery", "Vascular", 3.50, 5.80, 278, 2),
    # ═══ Radiology — X-ray ═══
    ("71046", "Chest X-ray 2 views", "Radiology", "Diagnostic X-ray", 0.18, 0.60, 29, 120),
    ("73560", "Knee X-ray 1-2 views", "Radiology", "Diagnostic X-ray", 0.17, 0.52, 25, 45),
    ("73030", "Shoulder X-ray 2+ views", "Radiology", "Diagnostic X-ray", 0.17, 0.52, 25, 30),
    ("72100", "Lumbosacral spine X-ray", "Radiology", "Diagnostic X-ray", 0.22, 0.71, 34, 28),
    ("70553", "Brain MRI w & w/o contrast", "Radiology", "MRI", 1.96, 5.98, 287, 8),
    # ═══ Radiology — CT ═══
    ("74177", "CT abdomen/pelvis w contrast", "Radiology", "CT", 1.74, 5.38, 258, 22),
    ("71260", "CT chest w contrast", "Radiology", "CT", 1.38, 4.27, 205, 18),
    ("70553", "MRI brain w & w/o contrast", "Radiology", "MRI", 1.96, 5.98, 287, 8),
    ("72148", "MRI lumbar spine w/o contrast", "Radiology", "MRI", 1.52, 4.80, 230, 15),
    ("73721", "MRI lower extremity joint", "Radiology", "MRI", 1.40, 4.40, 211, 10),
    ("70551", "MRI brain w/o contrast", "Radiology", "MRI", 1.52, 4.44, 213, 12),
    # ═══ Radiology — Ultrasound ═══
    ("76856", "Pelvic ultrasound complete", "Radiology", "Ultrasound", 0.74, 2.15, 103, 15),
    ("76700", "Abdominal ultrasound compl", "Radiology", "Ultrasound", 0.81, 2.31, 111, 18),
    ("93880", "Duplex scan extracranial", "Radiology", "Ultrasound", 0.50, 2.10, 101, 10),
    ("93925", "Duplex scan lower ext arteries", "Radiology", "Ultrasound", 0.50, 1.90, 91, 8),
    # ═══ Radiology — Nuclear / Radiation Therapy / Mammography ═══
    ("78452", "Myocardial perfusion SPECT", "Radiology", "Nuclear Medicine", 1.35, 6.50, 312, 5),
    ("78816", "PET scan whole body", "Radiology", "Nuclear Medicine", 1.80, 8.40, 403, 3),
    ("77067", "Screening mammography bilat", "Radiology", "Mammography", 0.69, 2.05, 98, 55),
    ("77066", "Diagnostic mammography bilat", "Radiology", "Mammography", 0.87, 2.55, 122, 12),
    ("77386", "IMRT radiation delivery", "Radiology", "Radiation Therapy", 0.35, 1.80, 86, 2),
    ("77385", "IMRT radiation simple", "Radiology", "Radiation Therapy", 0.30, 1.50, 72, 1.5),
    ("77263", "Radiation treatment planning", "Radiology", "Radiation Therapy", 3.63, 5.20, 250, 1),
    # ═══ Lab — Chemistry ═══
    ("80053", "Comprehensive metabolic panel", "Lab", "Chemistry", 0.00, 0.00, 14, 250),
    ("80048", "Basic metabolic panel", "Lab", "Chemistry", 0.00, 0.00, 11, 180),
    ("80061", "Lipid panel", "Lab", "Chemistry", 0.00, 0.00, 18, 120),
    ("82947", "Glucose blood test", "Lab", "Chemistry", 0.00, 0.00, 8, 160),
    ("83036", "Hemoglobin A1c", "Lab", "Chemistry", 0.00, 0.00, 13, 110),
    ("84443", "TSH blood test", "Lab", "Chemistry", 0.00, 0.00, 22, 95),
    ("82306", "Vitamin D 25-hydroxy", "Lab", "Chemistry", 0.00, 0.00, 40, 45),
    ("82728", "Ferritin blood test", "Lab", "Chemistry", 0.00, 0.00, 18, 35),
    ("82550", "CK/CPK total", "Lab", "Chemistry", 0.00, 0.00, 12, 20),
    # ═══ Lab — Hematology ═══
    ("85025", "CBC w auto diff", "Lab", "Hematology", 0.00, 0.00, 11, 280),
    ("85027", "CBC automated", "Lab", "Hematology", 0.00, 0.00, 9, 150),
    ("85610", "Prothrombin time (PT)", "Lab", "Hematology", 0.00, 0.00, 6, 55),
    ("85730", "Partial thromboplastin time", "Lab", "Hematology", 0.00, 0.00, 9, 30),
    ("85379", "D-dimer quantitative", "Lab", "Hematology", 0.00, 0.00, 15, 18),
    # ═══ Lab — Pathology ═══
    ("88305", "Surgical pathology, gross/micro", "Lab", "Pathology", 0.75, 1.51, 72, 40),
    ("88342", "Immunohistochemistry", "Lab", "Pathology", 0.60, 1.24, 60, 12),
    ("88312", "Special stain Group I", "Lab", "Pathology", 0.55, 1.10, 53, 8),
    # ═══ Lab — Molecular / Genetics ═══
    ("81479", "Unlisted molecular pathology", "Lab", "Molecular/Genetics", 0.00, 0.00, 350, 3),
    ("81225", "CYP2C19 gene analysis", "Lab", "Molecular/Genetics", 0.00, 0.00, 190, 2),
    ("81408", "Molecular path level 9", "Lab", "Molecular/Genetics", 0.00, 0.00, 580, 0.5),
    ("81528", "Oncology colorectal screening", "Lab", "Molecular/Genetics", 0.00, 0.00, 508, 1),
    # ═══ Medicine — Cardiology Dx ═══
    ("93000", "ECG 12-lead w interpret", "Medicine", "Cardiology Dx", 0.17, 0.56, 27, 120),
    ("93306", "TTE w Doppler complete", "Medicine", "Cardiology Dx", 1.50, 4.65, 223, 25),
    ("93351", "Stress echo complete", "Medicine", "Cardiology Dx", 1.75, 5.10, 245, 8),
    ("93458", "Left heart catheterization", "Medicine", "Cardiology Dx", 4.22, 9.80, 470, 3),
    ("93015", "Cardiovascular stress test", "Medicine", "Cardiology Dx", 0.75, 2.20, 106, 15),
    ("93279", "PM device interrogation", "Medicine", "Cardiology Dx", 0.52, 0.90, 43, 10),
    # ═══ Medicine — Pulmonary ═══
    ("94010", "Spirometry", "Medicine", "Pulmonary", 0.17, 0.62, 30, 25),
    ("94060", "Bronchodilator response", "Medicine", "Pulmonary", 0.17, 0.74, 36, 15),
    ("94726", "Plethysmography", "Medicine", "Pulmonary", 0.20, 0.82, 39, 5),
    ("94729", "DLCO diffusing capacity", "Medicine", "Pulmonary", 0.16, 0.57, 27, 4),
    # ═══ Medicine — GI ═══
    ("91035", "Esophageal motility study", "Medicine", "Gastroenterology", 1.50, 3.20, 154, 2),
    ("91038", "Esophageal pH monitoring 24h", "Medicine", "Gastroenterology", 0.85, 2.10, 101, 1.5),
    # ═══ Medicine — Nephrology/Dialysis ═══
    ("90935", "Hemodialysis one eval", "Medicine", "Nephrology/Dialysis", 0.55, 1.18, 57, 6),
    ("90937", "Hemodialysis repeated eval", "Medicine", "Nephrology/Dialysis", 0.87, 1.80, 86, 4),
    ("90945", "Peritoneal dialysis one eval", "Medicine", "Nephrology/Dialysis", 0.55, 1.10, 53, 2),
    ("90960", "ESRD monthly service 4+ visits", "Medicine", "Nephrology/Dialysis", 4.50, 6.80, 326, 2),
    # ═══ Medicine — Infusion/Injection ═══
    ("96413", "Chemo IV infusion first hour", "Medicine", "Infusion/Injection", 1.28, 2.35, 113, 3),
    ("96365", "IV infusion therapeutic 1st hr", "Medicine", "Infusion/Injection", 0.21, 0.70, 34, 20),
    ("96372", "Therapeutic injection SC/IM", "Medicine", "Infusion/Injection", 0.17, 0.47, 23, 65),
    ("96374", "Therapeutic injection IV push", "Medicine", "Infusion/Injection", 0.26, 0.62, 30, 25),
    ("J0585", "Botox per unit injection", "Medicine", "Infusion/Injection", 0.00, 0.00, 9, 5),
    ("J1745", "Infliximab injection 10mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 120, 1.5),
    ("J2507", "Pegfilgrastim 6mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 3800, 0.8),
    ("J9271", "Pembrolizumab injection", "Medicine", "Infusion/Injection", 0.00, 0.00, 9200, 0.4),
    ("J0129", "Abatacept injection", "Medicine", "Infusion/Injection", 0.00, 0.00, 1050, 0.6),
    # ═══ Medicine — Physical Therapy ═══
    ("97110", "Therapeutic exercises 15 min", "Medicine", "Physical Therapy", 0.40, 0.71, 34, 60),
    ("97140", "Manual therapy 15 min", "Medicine", "Physical Therapy", 0.43, 0.75, 36, 45),
    ("97530", "Therapeutic activities 15 min", "Medicine", "Physical Therapy", 0.44, 0.76, 36, 35),
    ("97161", "PT evaluation low complexity", "Medicine", "Physical Therapy", 1.20, 2.08, 100, 15),
    ("97162", "PT evaluation mod complexity", "Medicine", "Physical Therapy", 1.50, 2.58, 124, 12),
    ("97163", "PT evaluation high complexity", "Medicine", "Physical Therapy", 1.80, 3.08, 148, 5),
    # ═══ Medicine — Ophthalmology Dx ═══
    ("92014", "Eye exam estab comp", "Medicine", "Ophthalmology Dx", 1.10, 2.40, 115, 20),
    ("92134", "Retinal OCT scan", "Medicine", "Ophthalmology Dx", 0.00, 0.83, 40, 15),
    ("92083", "Visual field exam", "Medicine", "Ophthalmology Dx", 0.00, 0.62, 30, 10),
    # ═══ Medicine — Allergy ═══
    ("95165", "Allergy immunotherapy multi", "Medicine", "Allergy/Immunology", 0.10, 0.20, 10, 12),
    ("86235", "Nuclear antigen antibody", "Medicine", "Allergy/Immunology", 0.00, 0.00, 19, 8),
    # ═══ Anesthesia ═══
    ("00142", "Anesthesia lens surgery", "Anesthesia", "General Anesthesia", 5.00, 7.00, 336, 8),
    ("01402", "Anesthesia knee arthroplasty", "Anesthesia", "General Anesthesia", 7.00, 10.00, 480, 2),
    ("00810", "Anesthesia lower abd surgery", "Anesthesia", "General Anesthesia", 6.00, 8.50, 408, 3),
    ("01967", "Anesthesia for cesarean", "Anesthesia", "General Anesthesia", 7.00, 10.00, 480, 1.5),
    ("01996", "Daily hosp mgmt epidural", "Anesthesia", "Regional Anesthesia", 3.00, 4.20, 202, 2),
    ("64483", "Transforaminal epidural inj", "Anesthesia", "Pain Management", 3.18, 5.55, 266, 4),
    ("64493", "Facet joint injection lumbar", "Anesthesia", "Pain Management", 1.48, 3.16, 152, 5),
    ("20610", "Joint injection major", "Anesthesia", "Pain Management", 1.22, 2.10, 101, 15),
    ("64625", "Radiofrequency ablation lumbar", "Anesthesia", "Pain Management", 3.28, 5.82, 279, 2),
    ("62323", "Lumbar epidural injection", "Anesthesia", "Pain Management", 1.90, 3.80, 182, 6),
    # ═══ DME / Supply ═══
    ("L1843", "Knee orthosis adj post op", "DME/Supply", "Orthotics", 0.00, 0.00, 380, 2),
    ("L3000", "Foot orthotic longitudinal", "DME/Supply", "Orthotics", 0.00, 0.00, 45, 5),
    ("E0601", "CPAP device", "DME/Supply", "Oxygen/Respiratory", 0.00, 0.00, 85, 3),
    ("E0431", "Portable gaseous O2 system", "DME/Supply", "Oxygen/Respiratory", 0.00, 0.00, 55, 2),
    ("E0260", "Hospital bed semi-electric", "DME/Supply", "Orthotics", 0.00, 0.00, 165, 1),
    ("A4253", "Blood glucose test strips", "DME/Supply", "Diabetic Supply", 0.00, 0.00, 12, 50),
    ("E0607", "Home blood glucose monitor", "DME/Supply", "Diabetic Supply", 0.00, 0.00, 35, 4),
    # ═══ Behavioral Health ═══
    ("90834", "Psychotherapy 45 min", "Behavioral Health", "Psychotherapy", 1.50, 2.59, 124, 22),
    ("90837", "Psychotherapy 60 min", "Behavioral Health", "Psychotherapy", 2.10, 3.55, 170, 15),
    ("90832", "Psychotherapy 30 min", "Behavioral Health", "Psychotherapy", 1.00, 1.76, 85, 18),
    ("90847", "Family psychotherapy w patient", "Behavioral Health", "Psychotherapy", 1.75, 2.95, 142, 5),
    ("90853", "Group psychotherapy", "Behavioral Health", "Psychotherapy", 0.47, 0.88, 42, 8),
    ("90792", "Psychiatric diagnostic eval", "Behavioral Health", "Psychiatry", 2.80, 4.60, 221, 6),
    ("90833", "Psychotherapy add-on 30 min", "Behavioral Health", "Psychiatry", 0.95, 1.55, 74, 12),
    ("90836", "Psychotherapy add-on 45 min", "Behavioral Health", "Psychiatry", 1.40, 2.30, 110, 8),
    ("90839", "Crisis psychotherapy 60 min", "Behavioral Health", "Psychotherapy", 2.65, 4.15, 199, 2),
    ("H0015", "Substance abuse IOP per hr", "Behavioral Health", "Substance Abuse", 0.00, 0.00, 48, 4),
    ("H0004", "Behavioral health counseling", "Behavioral Health", "Substance Abuse", 0.00, 0.00, 35, 6),
    ("96132", "Neuropsych testing eval", "Behavioral Health", "Neuropsych Testing", 3.00, 4.80, 230, 1),
    ("96136", "Neuropsych test admin", "Behavioral Health", "Neuropsych Testing", 1.40, 2.30, 110, 1),
    # ═══ High-cost drugs (J-codes) ═══
    ("J9035", "Bevacizumab injection 10mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 680, 0.5),
    ("J9305", "Pemetrexed injection 10mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 4200, 0.3),
    ("J9299", "Nivolumab injection 1mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 3500, 0.3),
    ("J1300", "Eculizumab injection 10mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 6800, 0.1),
    ("J2350", "Ocrelizumab injection 1mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 2400, 0.3),
    ("J0517", "Benralizumab injection 1mg", "Medicine", "Infusion/Injection", 0.00, 0.00, 2800, 0.2),
    # ═══ Additional high-volume codes ═══
    ("99024", "Postoperative follow-up", "E&M", "Office Visit", 0.00, 0.00, 0, 40),
    ("99406", "Smoking cessation 3-10 min", "E&M", "Preventive", 0.24, 0.50, 24, 8),
    ("36415", "Venipuncture routine", "Lab", "Chemistry", 0.00, 0.17, 3, 300),
    ("81001", "Urinalysis w microscopy", "Lab", "Chemistry", 0.00, 0.00, 4, 80),
    ("87070", "Bacterial culture other", "Lab", "Microbiology", 0.00, 0.00, 10, 25),
    ("87491", "Chlamydia DNA probe", "Lab", "Microbiology", 0.00, 0.00, 36, 12),
    ("87081", "Bacterial culture screen", "Lab", "Microbiology", 0.00, 0.00, 9, 20),
    ("G0121", "Colorectal screen high risk", "Medicine", "Gastroenterology", 3.69, 6.13, 294, 5),
    ("G0105", "Colorectal screen hi risk ind", "Medicine", "Gastroenterology", 3.36, 5.58, 268, 3),
    ("G2211", "Visit complexity add-on", "E&M", "Office Visit", 0.33, 0.49, 16, 200),
    ("99417", "Prolonged office visit 15 min", "E&M", "Office Visit", 1.00, 1.50, 72, 30),
    ("99345", "Home visit new, high", "E&M", "Care Management", 3.86, 6.30, 302, 2),
    ("G0438", "Annual wellness visit initial", "E&M", "Preventive", 2.43, 3.90, 187, 20),
    ("G0439", "Annual wellness visit subseq", "E&M", "Preventive", 1.92, 3.12, 150, 35),
    ("90471", "Immunization admin 1st", "Medicine", "Allergy/Immunology", 0.17, 0.38, 18, 60),
    ("90658", "Influenza vaccine IIV4", "Medicine", "Allergy/Immunology", 0.00, 0.00, 20, 50),
]


def get_cpt_reference() -> pd.DataFrame:
    """Return CPT reference DataFrame."""
    df = pd.DataFrame(CPT_DATA, columns=[
        "cpt_code", "description", "category", "subcategory",
        "rvu_work", "rvu_total", "national_avg_allowed",
        "annual_utilization_per_1000",
    ])
    df = df.drop_duplicates(subset="cpt_code", keep="first")
    return df


STATES_10 = [
    {"abbr": "FL", "name": "Florida", "region": "Southeast", "population": 22_245_000, "medicare_pct": 0.22, "medicaid_pct": 0.18},
    {"abbr": "CA", "name": "California", "region": "West", "population": 38_965_000, "medicare_pct": 0.14, "medicaid_pct": 0.28},
    {"abbr": "TX", "name": "Texas", "region": "South Central", "population": 30_503_000, "medicare_pct": 0.13, "medicaid_pct": 0.20},
    {"abbr": "NY", "name": "New York", "region": "Northeast", "population": 19_571_000, "medicare_pct": 0.17, "medicaid_pct": 0.26},
    {"abbr": "PA", "name": "Pennsylvania", "region": "Northeast", "population": 12_962_000, "medicare_pct": 0.19, "medicaid_pct": 0.22},
    {"abbr": "IL", "name": "Illinois", "region": "Midwest", "population": 12_550_000, "medicare_pct": 0.16, "medicaid_pct": 0.24},
    {"abbr": "OH", "name": "Ohio", "region": "Midwest", "population": 11_780_000, "medicare_pct": 0.18, "medicaid_pct": 0.23},
    {"abbr": "GA", "name": "Georgia", "region": "Southeast", "population": 10_912_000, "medicare_pct": 0.14, "medicaid_pct": 0.17},
    {"abbr": "AZ", "name": "Arizona", "region": "West", "population": 7_360_000, "medicare_pct": 0.19, "medicaid_pct": 0.22},
    {"abbr": "NJ", "name": "New Jersey", "region": "Northeast", "population": 9_290_000, "medicare_pct": 0.16, "medicaid_pct": 0.19},
]


def get_states_reference() -> pd.DataFrame:
    return pd.DataFrame(STATES_10)
