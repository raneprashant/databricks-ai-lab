from dataclasses import dataclass
from datetime import date
from pathlib import Path


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GENERATED_DATA_ROOT = PROJECT_ROOT / "generated_data"


# ---------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------

RANDOM_SEED = 42


# ---------------------------------------------------------
# Synthetic business timeline
# ---------------------------------------------------------

DATA_START_DATE = date(2024, 1, 1)
DATA_END_DATE = date(2026, 9, 30)

# Allows us to create future-effective eligibility records.
FUTURE_COVERAGE_END_DATE = date(2027, 3, 31)


# ---------------------------------------------------------
# Scale definition
# ---------------------------------------------------------

@dataclass(frozen=True)
class ScaleConfig:
    products: int
    benefit_plans: int
    groups: int
    subgroups: int
    members: int
    eligibility: int
    practitioners: int
    suppliers: int
    supplier_locations: int
    practitioner_roles: int
    addresses: int
    entity_addresses: int
    claim_headers: int
    claim_lines: int

    @property
    def total_rows(self) -> int:
        return (
            self.products
            + self.benefit_plans
            + self.groups
            + self.subgroups
            + self.members
            + self.eligibility
            + self.practitioners
            + self.suppliers
            + self.supplier_locations
            + self.practitioner_roles
            + self.addresses
            + self.entity_addresses
            + self.claim_headers
            + self.claim_lines
        )


SCALES = {

    # Fast development/debug run.
    "smoke": ScaleConfig(
        products=8,
        benefit_plans=24,
        groups=40,
        subgroups=100,
        members=5_000,
        eligibility=15_000,
        practitioners=1_000,
        suppliers=100,
        supplier_locations=300,
        practitioner_roles=2_500,
        addresses=10_000,
        entity_addresses=17_000,
        claim_headers=10_000,
        claim_lines=30_000,
    ),

    # Useful for intermediate Spark testing.
    "medium": ScaleConfig(
        products=16,
        benefit_plans=60,
        groups=500,
        subgroups=1_500,
        members=75_000,
        eligibility=225_000,
        practitioners=20_000,
        suppliers=1_000,
        supplier_locations=4_000,
        practitioner_roles=60_000,
        addresses=140_000,
        entity_addresses=300_000,
        claim_headers=150_000,
        claim_lines=450_000,
    ),

    # Full project dataset.
    "full": ScaleConfig(
        products=1_000,
        benefit_plans=5_000,
        groups=25_000,
        subgroups=50_000,
        members=400_000,
        eligibility=1_200_000,
        practitioners=100_000,
        suppliers=8_000,
        supplier_locations=30_000,
        practitioner_roles=300_000,
        addresses=700_000,
        entity_addresses=1_600_000,
        claim_headers=800_000,
        claim_lines=2_800_000,
    ),
}


# ---------------------------------------------------------
# Number of records written to each source CSV file
#
# We intentionally generate multiple files so later
# Bronze ingestion behaves more like a real landing zone.
# ---------------------------------------------------------

ROWS_PER_FILE = {
    # Payer reference data
    "product": 1_000,
    "benefit_plan": 5_000,
    "group": 25_000,
    "subgroup": 50_000,

    # Member / eligibility
    "member": 100_000,
    "eligibility": 150_000,

    # Provider network
    "practitioner": 50_000,
    "supplier": 25_000,
    "supplier_location": 50_000,
    "practitioner_role": 100_000,

    # Address
    "address": 100_000,
    "entity_address": 150_000,

    # Claims
    "claim_header": 100_000,
    "claim_line": 250_000,
}


def get_scale(scale_name: str) -> ScaleConfig:
    try:
        return SCALES[scale_name.lower()]
    except KeyError:
        valid_scales = ", ".join(SCALES.keys())
        raise ValueError(
            f"Unknown scale '{scale_name}'. "
            f"Valid scales: {valid_scales}"
        )