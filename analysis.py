from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent


def load_data():
    data = pd.read_csv(ROOT / "data/bank-additional-full.csv", sep=";")
    if len(data) != 41188 or not set(data["y"]).issubset({"yes", "no"}):
        raise ValueError("Unexpected dataset")
    if data.isna().any().any() or (data["campaign"] < 1).any():
        raise ValueError("Invalid rows")
    data["subscribed"] = data["y"].eq("yes").astype(int)
    connection = sqlite3.connect(":memory:")
    data.to_sql("campaigns", connection, index=False)
    return data, connection


def query(connection, filename):
    return pd.read_sql_query((ROOT / "sql" / filename).read_text(encoding="utf-8"), connection)


def draw_rates(table, label, title, filename):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.bar(table[label].astype(str), table["conversion_pct"], color="#426b92", width=0.65)
    ax.set_ylabel("Subscription rate, %")
    ax.set_title(title, loc="left", fontsize=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.15)
    fig.tight_layout()
    fig.savefig(ROOT / "reports" / filename, dpi=150)
    return fig


def run():
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    data, connection = load_data()
    tables = {}
    try:
        for file in sorted((ROOT / "sql").glob("*.sql")):
            table = query(connection, file.name)
            table.to_csv(reports / f"{file.stem}.csv", index=False)
            tables[file.stem] = table
        quality = pd.DataFrame({"field": data.columns, "unknown_rows": [
            int(data[column].eq("unknown").sum()) for column in data.columns
        ]})
        quality.to_csv(reports / "data_quality.csv", index=False)
        print(tables["01_overview"].to_string(index=False))
        print("\nExact duplicate rows:", data.drop(columns="subscribed").duplicated().sum())
        for table, label, title, file in [
            ("02_contact", "contact", "Contact channel", "contact.png"),
            ("03_previous_outcome", "poutcome", "Previous campaign outcome", "previous.png"),
            ("04_contact_pressure", "contact_band", "Contacts in current campaign", "pressure.png")
        ]:
            plt.close(draw_rates(tables[table], label, title, file))
    finally:
        connection.close()
    return tables


if __name__ == "__main__":
    run()
