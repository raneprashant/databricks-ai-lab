"""
Project 01 - Healthcare Payer Data Platform
Module: reference_data.py

Purpose
-------
Provides reusable static synthetic reference values used by the
Project 01 data generators.

Reference Content Includes
--------------------------
- Male and female first names
- Last names
- Languages and marital statuses
- Supplier naming components and organization types
- Supplier ownership types
- Supplier Location types and naming values
- Place-of-service codes
- Practitioner credentials, suffixes, specialties, and license states
- Practitioner Role and PCP-related reference values
- Address street names, suffixes, and geographic regions
- Claim diagnosis categories and diagnosis codes
- Claim procedure/service-category profiles
- Specialty-to-diagnosis relationships

Usage
-----
This module is imported by other generators and is not normally
executed directly.

Important Notes
---------------
Reference values are synthetic and are intended for learning,
development, and testing only. They are not intended to represent
production healthcare code sets or real individuals/organizations.
"""




FIRST_NAMES_MALE = [
    "James", "John", "Robert", "Michael", "David",
    "William", "Richard", "Joseph", "Thomas", "Charles",
    "Daniel", "Matthew", "Anthony", "Mark", "Steven",
    "Andrew", "Joshua", "Christopher", "Ryan", "Kevin",
]

FIRST_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
    "Barbara", "Susan", "Jessica", "Sarah", "Karen",
    "Nancy", "Lisa", "Margaret", "Betty", "Sandra",
    "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
]

LANGUAGES = [
    "ENGLISH",
    "SPANISH",
    "CHINESE",
    "ARABIC",
    "FRENCH",
    "HINDI",
    "VIETNAMESE",
    "KOREAN",
]

MARITAL_STATUSES = [
    "SINGLE",
    "MARRIED",
    "DIVORCED",
    "WIDOWED",
]


# ---------------------------------------------------------
# Supplier reference values
# ---------------------------------------------------------

SUPPLIER_NAME_PREFIXES = [
    "Lakeside",
    "North Valley",
    "Western Regional",
    "Evergreen",
    "Riverside",
    "Mercy",
    "Oakwood",
    "Pinecrest",
    "Highland",
    "Grandview",
    "Summit",
    "Maple Grove",
    "Lakeview",
    "Northstar",
    "Heritage",
    "Cedar Valley",
    "Starlight",
    "Blue Ridge",
    "Riverbend",
    "Greenfield",
]

SUPPLIER_NAME_DESCRIPTORS = [
    "Regional",
    "Community",
    "University",
    "Memorial",
    "General",
    "Integrated",
    "Specialty",
    "Advanced",
    "Premier",
    "Comprehensive",
]

SUPPLIER_NAME_SUFFIXES = [
    "Health System",
    "Medical Center",
    "Healthcare Network",
    "Medical Group",
    "Hospital Network",
    "Behavioral Health",
    "Specialty Care",
    "Community Health",
]

SUPPLIER_TYPES = [
    "HOSPITAL_SYSTEM",
    "HOSPITAL_ORGANIZATION",
    "PHYSICIAN_GROUP",
    "BEHAVIORAL_HEALTH_ORG",
    "URGENT_CARE_ORG",
    "IMAGING_ORG",
    "LABORATORY_ORG",
    "SPECIALTY_CARE_ORG",
]

OWNERSHIP_TYPES = [
    "NON_PROFIT",
    "FOR_PROFIT",
    "GOVERNMENT",
    "ACADEMIC",
]


# ---------------------------------------------------------
# Supplier Location reference values
# ---------------------------------------------------------

SUPPLIER_LOCATION_TYPES = [
    "ACUTE_CARE_HOSPITAL",
    "OUTPATIENT_CENTER",
    "AMBULATORY_SURGERY_CENTER",
    "PHYSICIAN_OFFICE",
    "URGENT_CARE_CENTER",
    "IMAGING_CENTER",
    "LABORATORY",
    "BEHAVIORAL_HEALTH_CENTER",
    "REHABILITATION_CENTER",
    "SPECIALTY_CLINIC",
]

SUPPLIER_LOCATION_NAME_SUFFIXES = [
    "Main Campus",
    "North Campus",
    "South Campus",
    "East Campus",
    "West Campus",
    "Medical Pavilion",
    "Outpatient Center",
    "Specialty Center",
    "Community Clinic",
    "Medical Office",
    "Diagnostic Center",
    "Ambulatory Center",
]

PLACE_OF_SERVICE_CODES = [
    "11",  # Office
    "19",  # Off-campus outpatient hospital
    "21",  # Inpatient hospital
    "22",  # On-campus outpatient hospital
    "23",  # Emergency room
    "24",  # Ambulatory surgical center
    "49",  # Independent clinic
    "81",  # Independent laboratory
]

# ---------------------------------------------------------
# Practitioner reference values
# ---------------------------------------------------------

PRACTITIONER_CREDENTIALS = [
    "MD",
    "DO",
]

PRACTITIONER_SUFFIXES = [
    "",
    "",
    "",
    "",
    "Jr.",
    "Sr.",
    "III",
]

PRACTITIONER_SPECIALTIES = [
    "FAMILY_MEDICINE",
    "INTERNAL_MEDICINE",
    "PEDIATRICS",
    "CARDIOLOGY",
    "ORTHOPEDICS",
    "DERMATOLOGY",
    "NEUROLOGY",
    "PSYCHIATRY",
    "GENERAL_SURGERY",
    "OBSTETRICS_GYNECOLOGY",
    "EMERGENCY_MEDICINE",
    "ANESTHESIOLOGY",
    "RADIOLOGY",
    "PATHOLOGY",
    "ONCOLOGY",
    "GASTROENTEROLOGY",
    "ENDOCRINOLOGY",
    "NEPHROLOGY",
    "PULMONOLOGY",
    "RHEUMATOLOGY",
    "UROLOGY",
    "OPHTHALMOLOGY",
    "OTOLARYNGOLOGY",
]

US_LICENSE_STATES = [
    "NY",
    "PA",
    "OH",
    "NJ",
    "MA",
    "CT",
    "MI",
    "MD",
    "VA",
    "NC",
]


# ---------------------------------------------------------
# Practitioner Role / Affiliation reference values
# ---------------------------------------------------------

PRACTITIONER_ROLE_TYPES = [
    "PCP",
    "SPECIALIST",
    "ATTENDING_PHYSICIAN",
    "HOSPITALIST",
    "SURGEON",
    "CONSULTING_PHYSICIAN",
    "EMERGENCY_PHYSICIAN",
]

PCP_ELIGIBLE_SPECIALTIES = [
    "FAMILY_MEDICINE",
    "INTERNAL_MEDICINE",
    "PEDIATRICS",
]

PRACTITIONER_PANEL_STATUSES = [
    "OPEN",
    "LIMITED",
    "CLOSED",
    "NOT_APPLICABLE",
]


# ---------------------------------------------------------
# Address reference values
# ---------------------------------------------------------

STREET_NAMES = [
    "Oak",
    "Maple",
    "Cedar",
    "Pine",
    "Lake",
    "River",
    "Summit",
    "Heritage",
    "Meadow",
    "Valley",
    "Sunrise",
    "Park",
    "Main",
    "Market",
    "Union",
    "Liberty",
    "Franklin",
    "Washington",
    "Jefferson",
    "Elm",
    "Birch",
    "Willow",
    "Highland",
    "Orchard",
    "College",
    "Center",
    "Chestnut",
    "Walnut",
    "Grand",
    "Mill",
]

STREET_SUFFIXES = [
    "St",
    "Ave",
    "Rd",
    "Blvd",
    "Dr",
    "Ln",
    "Way",
    "Pkwy",
]


# city, state, county, 3-digit ZIP prefix
ADDRESS_REGIONS = [
    ("Buffalo", "NY", "Erie", "142"),
    ("Rochester", "NY", "Monroe", "146"),
    ("Syracuse", "NY", "Onondaga", "132"),
    ("Albany", "NY", "Albany", "122"),
    ("Cleveland", "OH", "Cuyahoga", "441"),
    ("Columbus", "OH", "Franklin", "432"),
    ("Pittsburgh", "PA", "Allegheny", "152"),
    ("Philadelphia", "PA", "Philadelphia", "191"),
    ("Detroit", "MI", "Wayne", "482"),
    ("Boston", "MA", "Suffolk", "021"),
    ("Hartford", "CT", "Hartford", "061"),
    ("Baltimore", "MD", "Baltimore City", "212"),
    ("Richmond", "VA", "Henrico", "232"),
    ("Charlotte", "NC", "Mecklenburg", "282"),
    ("Newark", "NJ", "Essex", "071"),
]


# ---------------------------------------------------------
# Claim reference values
#
# These are intentionally synthetic codes for our
# learning project.
# ---------------------------------------------------------

SPECIALTY_DIAGNOSIS_CATEGORY = {
    "FAMILY_MEDICINE": "GENERAL_MEDICAL",
    "INTERNAL_MEDICINE": "GENERAL_MEDICAL",
    "PEDIATRICS": "PEDIATRIC",
    "CARDIOLOGY": "CARDIOVASCULAR",
    "ORTHOPEDICS": "MUSCULOSKELETAL",
    "DERMATOLOGY": "DERMATOLOGY",
    "NEUROLOGY": "NEUROLOGY",
    "PSYCHIATRY": "BEHAVIORAL_HEALTH",
    "GENERAL_SURGERY": "SURGICAL",
    "OBSTETRICS_GYNECOLOGY": "WOMENS_HEALTH",
    "EMERGENCY_MEDICINE": "EMERGENCY",
    "ANESTHESIOLOGY": "SURGICAL",
    "RADIOLOGY": "IMAGING",
    "PATHOLOGY": "LABORATORY",
    "ONCOLOGY": "ONCOLOGY",
    "GASTROENTEROLOGY": "GASTROENTEROLOGY",
    "ENDOCRINOLOGY": "ENDOCRINOLOGY",
    "NEPHROLOGY": "RENAL",
    "PULMONOLOGY": "RESPIRATORY",
    "RHEUMATOLOGY": "RHEUMATOLOGY",
    "UROLOGY": "UROLOGY",
    "OPHTHALMOLOGY": "VISION",
    "OTOLARYNGOLOGY": "ENT",
}


CLAIM_DIAGNOSIS_CODES = {
    "GENERAL_MEDICAL": [
        "DX-GEN-001",
        "DX-GEN-002",
        "DX-GEN-003",
    ],
    "PEDIATRIC": [
        "DX-PED-001",
        "DX-PED-002",
        "DX-PED-003",
    ],
    "CARDIOVASCULAR": [
        "DX-CAR-001",
        "DX-CAR-002",
        "DX-CAR-003",
    ],
    "MUSCULOSKELETAL": [
        "DX-MSK-001",
        "DX-MSK-002",
        "DX-MSK-003",
    ],
    "DERMATOLOGY": [
        "DX-DER-001",
        "DX-DER-002",
    ],
    "NEUROLOGY": [
        "DX-NEU-001",
        "DX-NEU-002",
    ],
    "BEHAVIORAL_HEALTH": [
        "DX-BEH-001",
        "DX-BEH-002",
        "DX-BEH-003",
    ],
    "SURGICAL": [
        "DX-SUR-001",
        "DX-SUR-002",
    ],
    "WOMENS_HEALTH": [
        "DX-WH-001",
        "DX-WH-002",
    ],
    "EMERGENCY": [
        "DX-ER-001",
        "DX-ER-002",
        "DX-ER-003",
    ],
    "IMAGING": [
        "DX-IMG-001",
        "DX-IMG-002",
    ],
    "LABORATORY": [
        "DX-LAB-001",
        "DX-LAB-002",
    ],
    "ONCOLOGY": [
        "DX-ONC-001",
        "DX-ONC-002",
    ],
    "GASTROENTEROLOGY": [
        "DX-GI-001",
        "DX-GI-002",
    ],
    "ENDOCRINOLOGY": [
        "DX-END-001",
        "DX-END-002",
    ],
    "RENAL": [
        "DX-REN-001",
        "DX-REN-002",
    ],
    "RESPIRATORY": [
        "DX-RESP-001",
        "DX-RESP-002",
    ],
    "RHEUMATOLOGY": [
        "DX-RHE-001",
        "DX-RHE-002",
    ],
    "UROLOGY": [
        "DX-URO-001",
        "DX-URO-002",
    ],
    "VISION": [
        "DX-VIS-001",
        "DX-VIS-002",
    ],
    "ENT": [
        "DX-ENT-001",
        "DX-ENT-002",
    ],
}


CLAIM_PROCEDURE_PROFILES = {
    "OFFICE_VISIT": {
        "codes": [
            "PROC-OV-001",
            "PROC-OV-002",
            "PROC-OV-003",
        ],
        "min_billed": 90,
        "max_billed": 350,
        "revenue_code": "",
    },
    "PREVENTIVE": {
        "codes": [
            "PROC-PREV-001",
            "PROC-PREV-002",
        ],
        "min_billed": 100,
        "max_billed": 450,
        "revenue_code": "",
    },
    "SPECIALTY_VISIT": {
        "codes": [
            "PROC-SP-001",
            "PROC-SP-002",
            "PROC-SP-003",
        ],
        "min_billed": 150,
        "max_billed": 650,
        "revenue_code": "",
    },
    "LAB": {
        "codes": [
            "PROC-LAB-001",
            "PROC-LAB-002",
            "PROC-LAB-003",
        ],
        "min_billed": 25,
        "max_billed": 350,
        "revenue_code": "REV-LAB",
    },
    "IMAGING": {
        "codes": [
            "PROC-IMG-001",
            "PROC-IMG-002",
            "PROC-IMG-003",
        ],
        "min_billed": 175,
        "max_billed": 2500,
        "revenue_code": "REV-IMG",
    },
    "SURGERY": {
        "codes": [
            "PROC-SUR-001",
            "PROC-SUR-002",
            "PROC-SUR-003",
        ],
        "min_billed": 1000,
        "max_billed": 12000,
        "revenue_code": "REV-SUR",
    },
    "EMERGENCY": {
        "codes": [
            "PROC-ER-001",
            "PROC-ER-002",
            "PROC-ER-003",
        ],
        "min_billed": 400,
        "max_billed": 4000,
        "revenue_code": "REV-ER",
    },
    "INPATIENT": {
        "codes": [
            "PROC-IP-001",
            "PROC-IP-002",
            "PROC-IP-003",
        ],
        "min_billed": 800,
        "max_billed": 6500,
        "revenue_code": "REV-IP",
    },
    "BEHAVIORAL_HEALTH": {
        "codes": [
            "PROC-BEH-001",
            "PROC-BEH-002",
        ],
        "min_billed": 100,
        "max_billed": 650,
        "revenue_code": "REV-BEH",
    },
    "MATERNITY": {
        "codes": [
            "PROC-MAT-001",
            "PROC-MAT-002",
        ],
        "min_billed": 300,
        "max_billed": 3000,
        "revenue_code": "REV-MAT",
    },
}