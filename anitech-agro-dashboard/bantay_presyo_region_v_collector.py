#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parent
REGION_ID = "050000000"
COMMODITY_IDS = range(1, 11)
REQUEST_DELAY_SECONDS = 1
HEADER_ENDPOINT = "http://www.bantaypresyo.da.gov.ph/tbl_price_get_comm_header.php"
DATA_ENDPOINT = "http://www.bantaypresyo.da.gov.ph/tbl_price_get_comm_price.php"
DATE_ENDPOINT = "http://www.bantaypresyo.da.gov.ph/tbl_price_get_date_rice.php"
DEFAULT_OUTPUT = "bantay_presyo_region_v_legazpi_naga.csv"
DEFAULT_ML_OUTPUT = str(Path("ml_service") / "data" / "bantay_presyo_region_v_legazpi_naga_ml.csv")
TARGET_MARKETS = (
    "LEGAZPI CITY PUBLIC MARKET",
    "NAGA PEOPLE'S MALL",
)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded",
}

COMMODITY_NAME_MAP = {
    "COMMERCIAL (LOCAL) Regular Milled": {
        "crop_name": "commercial milled rice",
        "ml_crop": "Rice",
    },
    "Watermelon": {
        "crop_name": "watermelon",
        "ml_crop": "Watermelon",
    },
    "Melon": {
        "crop_name": "melon",
        "ml_crop": "Melon",
    },
    "Calamansi": {
        "crop_name": "calamansi",
        "ml_crop": "Calamansi",
    },
    "Ampalaya": {
        "crop_name": "ampalaya",
        "ml_crop": "Ampalaya",
    },
    "Squash": {
        "crop_name": "kalabasa",
        "ml_crop": "Squash",
    },
    "Pechay (Native)": {
        "crop_name": "pechay",
        "ml_crop": "Chinese Cabbage",
    },
    "Sitao": {
        "crop_name": "sitao",
        "ml_crop": "String Beans",
    },
    "Eggplant": {
        "crop_name": "talong",
        "ml_crop": "Eggplant",
    },
    "Cabbage (Scorpio)": {
        "crop_name": "cabbage",
        "ml_crop": "Cabbage",
    },
    "Garlic(Imported)": {
        "crop_name": "garlic",
        "ml_crop": "Garlic",
    },
    "Red Onion": {
        "crop_name": "red onion",
        "ml_crop": "Red Onion",
    },
}


def fetch_fragment(session: requests.Session, url: str, commodity_id: int, count: str = "10") -> str:
    payload = {
        "region": REGION_ID,
        "commodity": str(commodity_id),
        "count": count,
    }
    response = session.post(url, data=payload, timeout=30)
    response.raise_for_status()
    return response.text


def parse_headers(html_fragment: str) -> list[str]:
    soup = BeautifulSoup(html_fragment, "html.parser")
    cells = [cell.get_text(" ", strip=True) for cell in soup.find_all(["th", "td"])]
    return [cell for cell in cells if cell]


def parse_price_rows(html_fragment: str, headers: list[str], commodity_id: int, as_of_date: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html_fragment, "html.parser")
    rows: list[dict[str, str]] = []

    for row_index, tr in enumerate(soup.find_all("tr"), start=1):
        cells = [cell.get_text(" ", strip=True) for cell in tr.find_all("td")]
        if not cells or len(cells) != len(headers):
            continue

        row_data = {headers[index]: value for index, value in enumerate(cells)}
        row_data["region_id"] = REGION_ID
        row_data["commodity_id"] = str(commodity_id)
        row_data["as_of_date"] = as_of_date
        row_data["row_number"] = row_index
        rows.append(row_data)

    return rows


def parse_numeric(value: str) -> float | None:
    cleaned = str(value or "").strip()
    if not cleaned or cleaned.upper() == "N/A":
        return None
    try:
        return float(cleaned.replace(",", ""))
    except ValueError:
        return None


def build_filtered_dataframe(all_rows: list[dict[str, str]]) -> pd.DataFrame:
    filtered_rows: list[dict[str, object]] = []

    for row in all_rows:
        source_name = row.get("COMMODITY", "")
        if source_name not in COMMODITY_NAME_MAP:
            continue

        legazpi_price = parse_numeric(row.get(TARGET_MARKETS[0], ""))
        naga_price = parse_numeric(row.get(TARGET_MARKETS[1], ""))
        available_prices = [price for price in (legazpi_price, naga_price) if price is not None]
        if not available_prices:
            continue

        as_of = datetime.strptime(str(row["as_of_date"]).strip(), "%B %d, %Y").date()
        crop_name = COMMODITY_NAME_MAP[source_name]["crop_name"]
        ml_crop = COMMODITY_NAME_MAP[source_name]["ml_crop"]
        average_price = Decimal(str(sum(available_prices) / len(available_prices))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        filtered_rows.append({
            "date": as_of.isoformat(),
            "year": as_of.year,
            "month": as_of.month,
            "region_id": REGION_ID,
            "commodity_id": row["commodity_id"],
            "source_row_name": source_name,
            "crop_name": crop_name,
            "ml_crop": ml_crop,
            "specification": row.get("SPECIFICATIONS", ""),
            "legazpi_city_public_market": legazpi_price,
            "naga_peoples_mall": naga_price,
            "market_count_used": len(available_prices),
            "average_price": float(average_price),
            "location": "Bicol",
            "source_markets": ", ".join(market for market, price in ((TARGET_MARKETS[0], legazpi_price), (TARGET_MARKETS[1], naga_price)) if price is not None),
        })

    return pd.DataFrame(filtered_rows)


def build_ml_dataframe(filtered_df: pd.DataFrame) -> pd.DataFrame:
    if filtered_df.empty:
        return pd.DataFrame()

    ml_df = filtered_df.copy()
    ml_df["crop"] = ml_df["ml_crop"]
    ml_df["price_per_kg"] = ml_df["average_price"]
    ml_df["rainfall_mm"] = ml_df["month"].apply(lambda month: 310.0 if 6 <= int(month) <= 11 else 72.0)
    ml_df["temperature_c"] = ml_df["month"].apply(lambda month: 27.0 if 6 <= int(month) <= 11 else 30.0)
    ml_df["humidity_pct"] = ml_df["month"].apply(lambda month: 81.0 if 6 <= int(month) <= 11 else 67.0)
    ml_df["soil_ph"] = 6.1
    ml_df["yield_kg_ha"] = 3500.0

    return ml_df[
        [
            "date",
            "year",
            "month",
            "location",
            "crop",
            "rainfall_mm",
            "temperature_c",
            "humidity_pct",
            "soil_ph",
            "yield_kg_ha",
            "price_per_kg",
            "crop_name",
            "legazpi_city_public_market",
            "naga_peoples_mall",
            "market_count_used",
            "source_markets",
            "source_row_name",
            "commodity_id",
        ]
    ].sort_values(["crop", "date"])


def dataframes_match(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    if left.empty and right.empty:
        return True
    if sorted(left.columns.tolist()) != sorted(right.columns.tolist()):
        return False

    normalized_left = left.reindex(sorted(left.columns), axis=1).sort_values(sorted(left.columns)).reset_index(drop=True)
    normalized_right = right.reindex(sorted(right.columns), axis=1).sort_values(sorted(right.columns)).reset_index(drop=True)
    return normalized_left.equals(normalized_right)


def collect_region_v_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    session = requests.Session()
    session.trust_env = False
    session.headers.update(REQUEST_HEADERS)

    all_rows: list[dict[str, str]] = []

    for commodity_id in COMMODITY_IDS:
        header_fragment = fetch_fragment(session, HEADER_ENDPOINT, commodity_id)
        headers = parse_headers(header_fragment)
        if not headers:
            raise RuntimeError(f"No headers returned for commodity {commodity_id}")

        as_of_date = fetch_fragment(session, DATE_ENDPOINT, commodity_id).strip()
        price_fragment = fetch_fragment(session, DATA_ENDPOINT, commodity_id, count=str(max(len(headers) - 2, 10)))
        parsed_rows = parse_price_rows(price_fragment, headers, commodity_id, as_of_date)
        all_rows.extend(parsed_rows)
        print(f"Commodity {commodity_id}: collected {len(parsed_rows)} rows as of {as_of_date}")
        time.sleep(REQUEST_DELAY_SECONDS)

    filtered_df = build_filtered_dataframe(all_rows)
    ml_df = build_ml_dataframe(filtered_df)
    return filtered_df, ml_df


def sync_market_prices(filtered_df: pd.DataFrame) -> int:
    if filtered_df.empty:
        return 0

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anitech.settings")
    import django

    django.setup()

    from market.models import MarketPrice

    synced = 0
    for row in filtered_df.itertuples(index=False):
        source_date = datetime.strptime(row.date, "%Y-%m-%d").date()
        current_price = Decimal(str(row.average_price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        record, created = MarketPrice.objects.get_or_create(
            crop_name=row.crop_name,
            date=source_date,
            defaults={
                "current_price": current_price,
                "unit": "per kg",
            },
        )

        if created:
            MarketPrice.objects.filter(pk=record.pk).update(date=source_date)
            synced += 1
            continue

        record.current_price = current_price
        record.unit = "per kg"
        if record.previous_price is None:
            previous = (
                MarketPrice.objects.filter(crop_name__iexact=row.crop_name)
                .exclude(pk=record.pk)
                .order_by("-date", "-last_updated")
                .first()
            )
            if previous:
                record.previous_price = previous.current_price
        record.save()
        MarketPrice.objects.filter(pk=record.pk).update(date=source_date)
        synced += 1

    return synced


def retrain_market_model() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anitech.settings")
    from ml_service.market_price_predictor import train_advanced_price_model

    train_advanced_price_model()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect Region V Bantay Presyo data for Legazpi and Naga only, export CSVs, sync MarketPrice, and retrain the market model."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Filtered Legazpi/Naga CSV path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--ml-output",
        default=DEFAULT_ML_OUTPUT,
        help=f"ML-ready CSV path. Default: {DEFAULT_ML_OUTPUT}",
    )
    parser.add_argument(
        "--no-sync-db",
        action="store_true",
        help="Do not sync the collected averages into the MarketPrice table.",
    )
    parser.add_argument(
        "--skip-retrain",
        action="store_true",
        help="Do not retrain the market price model after saving the ML-ready CSV.",
    )
    args = parser.parse_args()

    output_path = (PROJECT_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()
    ml_output_path = (PROJECT_ROOT / args.ml_output).resolve() if not Path(args.ml_output).is_absolute() else Path(args.ml_output).resolve()

    try:
        filtered_df, ml_df = collect_region_v_data()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    if filtered_df.empty or ml_df.empty:
        print("No Legazpi/Naga rows were collected for the target commodities.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ml_output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_filtered_df = pd.read_csv(output_path) if output_path.exists() else pd.DataFrame()
    existing_ml_df = pd.read_csv(ml_output_path) if ml_output_path.exists() else pd.DataFrame()
    filtered_changed = not dataframes_match(filtered_df, existing_filtered_df)
    ml_changed = not dataframes_match(ml_df, existing_ml_df)

    if filtered_changed:
        filtered_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Saved {len(filtered_df)} city-filtered rows to {output_path}")
    else:
        print(f"No Legazpi/Naga source changes detected in {output_path.name}")

    if ml_changed:
        ml_df.to_csv(ml_output_path, index=False, encoding="utf-8-sig")
        print(f"Saved {len(ml_df)} ML-ready rows to {ml_output_path}")
    else:
        print(f"No ML dataset changes detected in {ml_output_path.name}")

    if not args.no_sync_db:
        try:
            synced = sync_market_prices(filtered_df)
            print(f"Synchronized {synced} MarketPrice rows for charts and DB-backed forecasts")
        except Exception as exc:
            print(f"Database sync failed: {exc}", file=sys.stderr)
            return 1

    if not args.skip_retrain and ml_changed:
        try:
            retrain_market_model()
            print("Retrained market price model using the updated ML dataset")
        except Exception as exc:
            print(f"Model retraining failed: {exc}", file=sys.stderr)
            return 1
    elif not args.skip_retrain:
        print("Skipped retraining because the ML dataset did not change")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
