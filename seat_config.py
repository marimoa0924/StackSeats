from __future__ import annotations

SEAT_LAYOUT: dict[str, dict] = {
    "VIP": {
        "rows": {"A": 6, "B": 8},
        "price": 8000,
        "color": "#FFD700",
        "label": "VIP",
    },
    "S": {
        "rows": {"C": 10, "D": 10},
        "price": 5000,
        "color": "#4FC3F7",
        "label": "S",
    },
    "A": {
        "rows": {"E": 12, "F": 12},
        "price": 3000,
        "color": "#A5D6A7",
        "label": "A",
    },
}

ROW_ORDER: list[str] = ["A", "B", "C", "D", "E", "F"]

ROW_TO_GRADE: dict[str, str] = {
    row: grade
    for grade, cfg in SEAT_LAYOUT.items()
    for row in cfg["rows"]
}

SEAT_TO_GRADE: dict[str, str] = {
    f"{row}-{n}": grade
    for grade, cfg in SEAT_LAYOUT.items()
    for row, cnt in cfg["rows"].items()
    for n in range(1, cnt + 1)
}

ALL_GRADES: list[str] = ["VIP", "S", "A"]

INITIAL_CASH: int = 50_000
CHARGE_AMOUNT: int = 10_000
