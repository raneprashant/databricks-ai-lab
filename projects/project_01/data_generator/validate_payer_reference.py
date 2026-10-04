import csv
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

DATA_ROOT = (
    PROJECT_ROOT
    / "generated_data"
    / "smoke"
)


def load_rows(
    folder_name: str,
    pattern: str,
):

    rows = []

    folder = (
        DATA_ROOT
        / folder_name
    )

    for file_path in sorted(
        folder.glob(pattern)
    ):

        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as handle:

            rows.extend(
                csv.DictReader(
                    handle
                )
            )

    return rows


def main():

    products = load_rows(
        "product",
        "product_*.csv",
    )

    plans = load_rows(
        "benefit_plan",
        "benefit_plan_*.csv",
    )

    groups = load_rows(
        "group",
        "group_*.csv",
    )

    subgroups = load_rows(
        "subgroup",
        "subgroup_*.csv",
    )

    product_lookup = {
        row["product_id"]: row
        for row in products
    }

    plan_lookup = {
        row["benefit_plan_id"]: row
        for row in plans
    }

    group_lookup = {
        row["group_id"]: row
        for row in groups
    }

    errors = []

    for plan in plans:

        if (
            plan["product_id"]
            not in product_lookup
        ):

            errors.append(
                "Missing Product for "
                f"{plan['benefit_plan_id']}"
            )

    for subgroup in subgroups:

        group = group_lookup.get(
            subgroup["group_id"]
        )

        plan = plan_lookup.get(
            subgroup[
                "benefit_plan_id"
            ]
        )

        if not group:

            errors.append(
                "Missing Group for "
                f"{subgroup['subgroup_id']}"
            )

            continue

        if not plan:

            errors.append(
                "Missing Benefit Plan for "
                f"{subgroup['subgroup_id']}"
            )

            continue

        product = product_lookup[
            plan["product_id"]
        ]

        if (
            group["line_of_business"]
            != product[
                "line_of_business"
            ]
        ):

            errors.append(
                "LOB mismatch for "
                f"{subgroup['subgroup_id']}"
            )

    print()
    print("=" * 70)
    print(
        "PAYER REFERENCE VALIDATION"
    )
    print("=" * 70)

    print(
        f"Products      : "
        f"{len(products):,}"
    )

    print(
        f"Benefit Plans : "
        f"{len(plans):,}"
    )

    print(
        f"Groups        : "
        f"{len(groups):,}"
    )

    print(
        f"Subgroups     : "
        f"{len(subgroups):,}"
    )

    print(
        f"Errors        : "
        f"{len(errors):,}"
    )

    print("-" * 70)

    if errors:

        print(
            "PAYER REFERENCE VALIDATION FAILED"
        )

        for error in errors[:20]:
            print(
                error
            )

    else:

        print(
            "PAYER REFERENCE VALIDATION PASSED"
        )

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()