"""
Cleans and standardizes raw expense data into the schema the rest of the
pipeline expects. When real demo reports arrive, this is the file to edit --
update COLUMN_MAP to point at whatever the real column headers are.
"""
import pandas as pd

# Map "whatever the source file calls it" -> "what our pipeline calls it"
# Update the left-hand side once you see the real demo report headers.
COLUMN_MAP = {
    "transaction_id": "transaction_id",
    "date": "date",
    "department": "department",
    "expense_category": "expense_category",
    "vendor": "vendor",
    "amount_inr": "amount_inr",
    "cost_center": "cost_center",
    "approved_by": "approved_by",
    "description": "description",
}


def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={v: k for k, v in COLUMN_MAP.items() if v in df.columns})

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["date", "amount_inr"])
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} rows with missing date/amount")

    ACRONYMS = {"Hr": "HR", "It": "IT", "Hse": "HSE"}
    df["department"] = df["department"].astype(str).str.strip().str.title().replace(ACRONYMS)
    df["expense_category"] = df["expense_category"].astype(str).str.strip()
    df["vendor"] = df["vendor"].astype(str).str.strip()

    df["amount_inr"] = df["amount_inr"].abs()  # guard against negative entries
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.weekday >= 5

    df = df.drop_duplicates(subset=["transaction_id"])
    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = load_and_clean("data/raw_expenses.csv")
    df.to_csv("data/cleaned_expenses.csv", index=False)
    print(f"Cleaned dataset: {len(df)} rows -> data/cleaned_expenses.csv")
    print(df.dtypes)
