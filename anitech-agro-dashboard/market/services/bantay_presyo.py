from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from html import unescape
import logging
from pathlib import Path
import re
from statistics import mean
import threading
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.db import close_old_connections
from django.utils import timezone

from market.models import MarketPrice


logger = logging.getLogger(__name__)

BASE_URL = "http://www.bantaypresyo.da.gov.ph"
REGION_BICOL = "050000000"
TARGET_MARKETS = {
    "LEGAZPI CITY PUBLIC MARKET": "legazpi_city_public_market",
    "NAGA PEOPLE'S MALL": "naga_peoples_mall",
}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FILTERED_CSV_PATH = PROJECT_ROOT / "bantay_presyo_region_v_legazpi_naga.csv"
ML_CSV_PATH = PROJECT_ROOT / "ml_service" / "data" / "bantay_presyo_region_v_legazpi_naga_ml.csv"

MARKET_DATA_VERSION_KEY = "market_data_version"
MARKET_SYNC_STATUS_KEY = "market_bantay_presyo_sync_status"
MARKET_SYNC_LOCK_KEY = "market_bantay_presyo_sync_lock"
BANTAY_PRESYO_STALE_AFTER_SECONDS = 900
SYNC_LOCK_TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class TargetCommodity:
    commodity_id: str
    output_name: str
    source_row: str
    notes: str = ""


TARGET_COMMODITIES = (
    TargetCommodity("1", "commercial milled rice", "COMMERCIAL (LOCAL) Regular Milled"),
    TargetCommodity("5", "watermelon", "Watermelon"),
    TargetCommodity("5", "melon", "Melon"),
    TargetCommodity("5", "calamansi", "Calamansi"),
    TargetCommodity("7", "ampalaya", "Ampalaya"),
    TargetCommodity("7", "kalabasa", "Squash"),
    TargetCommodity("7", "pechay", "Pechay (Native)"),
    TargetCommodity("7", "pipino", "Cucumber"),
    TargetCommodity("7", "sitao", "Sitao"),
    TargetCommodity("7", "talong", "Eggplant"),
    TargetCommodity("7", "upo", "Bottle Gourd"),
    TargetCommodity("7", "okra", "Okra"),
    TargetCommodity("6", "cabbage", "Cabbage (Scorpio)"),
    TargetCommodity("6", "lettuce", "Lettuce (Iceberg)"),
    TargetCommodity("9", "garlic", "Garlic(Imported)"),
    TargetCommodity("9", "red onion", "Red Onion"),
)


def get_market_data_version():
    return cache.get(MARKET_DATA_VERSION_KEY, 1)


def bump_market_data_version():
    next_version = int(get_market_data_version()) + 1
    cache.set(MARKET_DATA_VERSION_KEY, next_version, None)
    cache.delete("all_crop_names")
    cache.delete("all_crop_names_for_ml")
    return next_version


def get_market_sync_status():
    status = cache.get(MARKET_SYNC_STATUS_KEY, {}) or {}
    latest_record = MarketPrice.objects.order_by("-date", "-last_updated").first()
    latest_synced_at = status.get("last_success_at")
    if latest_record and not latest_synced_at:
        latest_synced_at = latest_record.last_updated.isoformat()

    return {
        "is_syncing": bool(status.get("is_syncing")),
        "last_success_at": latest_synced_at,
        "last_attempt_at": status.get("last_attempt_at"),
        "last_error": status.get("last_error"),
        "last_source_date": status.get("last_source_date"),
        "csv_ready": _market_csv_exports_exist(),
        "has_market_rows": MarketPrice.objects.exists(),
    }


def is_market_data_stale(stale_after_seconds: int = BANTAY_PRESYO_STALE_AFTER_SECONDS):
    status = get_market_sync_status()
    last_success_at = status.get("last_success_at")
    if not last_success_at:
        return True

    try:
        last_sync = datetime.fromisoformat(last_success_at)
    except ValueError:
        return True

    if timezone.is_naive(last_sync):
        last_sync = timezone.make_aware(last_sync, timezone.get_current_timezone())

    return (timezone.now() - last_sync).total_seconds() >= stale_after_seconds


def ensure_market_price_data_available():
    needs_recovery_sync = (not MarketPrice.objects.exists()) or (not _market_csv_exports_exist())
    if not needs_recovery_sync:
        return {"recovered": False, "reason": None}

    result = sync_bantay_presyo_market_prices(force=True)
    return {
        "recovered": result.get("status") == "success",
        "reason": "missing_db_rows_or_csv",
        "sync_result": result,
    }


def sync_bantay_presyo_market_prices(force: bool = False):
    if not force and cache.get(MARKET_SYNC_LOCK_KEY):
        return {"started": False, "status": "skipped", "reason": "sync_in_progress"}

    lock_acquired = cache.add(MARKET_SYNC_LOCK_KEY, "1", SYNC_LOCK_TIMEOUT_SECONDS)
    if not lock_acquired and not force:
        return {"started": False, "status": "skipped", "reason": "sync_in_progress"}

    now_iso = timezone.now().isoformat()
    previous_status = cache.get(MARKET_SYNC_STATUS_KEY, {}) or {}
    cache.set(
        MARKET_SYNC_STATUS_KEY,
        {
            **previous_status,
            "is_syncing": True,
            "last_attempt_at": now_iso,
            "last_error": None,
        },
        None,
    )

    try:
        source_date = _fetch_source_date("1")
        datasets = {
            commodity_id: _fetch_dataset(commodity_id)
            for commodity_id in sorted({item.commodity_id for item in TARGET_COMMODITIES})
        }

        updated = 0
        created = 0
        skipped = []
        export_rows = []

        for target in TARGET_COMMODITIES:
            dataset = datasets[target.commodity_id]
            row = dataset["rows"].get(target.source_row.lower())
            if not row:
                skipped.append(f"{target.output_name}: source row '{target.source_row}' not found")
                continue

            market_prices = {}
            for market_name in TARGET_MARKETS:
                parsed_value = _parse_price(row.get(market_name, ""))
                if parsed_value is not None:
                    market_prices[market_name] = parsed_value

            if not market_prices:
                skipped.append(f"{target.output_name}: no usable Legazpi/Naga price")
                continue

            resolved_price = Decimal(str(mean(market_prices.values()))).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            export_rows.append(
                _build_export_row(
                    target=target,
                    row=row,
                    source_date=source_date,
                    market_prices=market_prices,
                    average_price=resolved_price,
                )
            )

            record, was_created = MarketPrice.objects.get_or_create(
                crop_name=target.output_name,
                date=source_date.date(),
                defaults={
                    "current_price": resolved_price,
                    "unit": "per kg",
                },
            )

            if was_created:
                MarketPrice.objects.filter(pk=record.pk).update(date=source_date.date())
                created += 1
            else:
                record.current_price = resolved_price
                record.unit = "per kg"
                if record.previous_price is None:
                    latest_previous = (
                        MarketPrice.objects.filter(crop_name__iexact=target.output_name)
                        .exclude(pk=record.pk)
                        .order_by("-date", "-last_updated")
                        .first()
                    )
                    if latest_previous:
                        record.previous_price = latest_previous.current_price
                record.save()
                MarketPrice.objects.filter(pk=record.pk).update(date=source_date.date())
                updated += 1

        _write_market_csv_exports(export_rows)

        bump_market_data_version()
        cache.set(
            MARKET_SYNC_STATUS_KEY,
            {
                "is_syncing": False,
                "last_attempt_at": now_iso,
                "last_success_at": timezone.now().isoformat(),
                "last_error": None,
                "last_source_date": source_date.date().isoformat(),
                "created": created,
                "updated": updated,
                "skipped": len(skipped),
            },
            None,
        )
        return {
            "started": True,
            "status": "success",
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "source_date": source_date.date().isoformat(),
        }
    except Exception as exc:
        logger.exception("Bantay Presyo sync failed")
        cache.set(
            MARKET_SYNC_STATUS_KEY,
            {
                **previous_status,
                "is_syncing": False,
                "last_attempt_at": now_iso,
                "last_error": str(exc),
            },
            None,
        )
        return {"started": True, "status": "error", "error": str(exc)}
    finally:
        cache.delete(MARKET_SYNC_LOCK_KEY)


def _run_sync_in_background(force: bool):
    close_old_connections()
    try:
        sync_bantay_presyo_market_prices(force=force)
    finally:
        close_old_connections()


def trigger_bantay_presyo_sync_async(force: bool = False, only_if_stale: bool = True):
    if only_if_stale and not force and not is_market_data_stale():
        return False
    if cache.get(MARKET_SYNC_LOCK_KEY):
        return False

    worker = threading.Thread(
        target=_run_sync_in_background,
        kwargs={"force": force},
        daemon=True,
        name="bantay-presyo-sync",
    )
    worker.start()
    return True


def _fetch_source_date(commodity_id: str):
    response = _post("tbl_price_get_date_rice.php", {"region": REGION_BICOL, "commodity": commodity_id})
    return datetime.strptime(response.strip(), "%B %d, %Y")


def _fetch_dataset(commodity_id: str):
    header_html = _post("tbl_price_get_comm_header.php", {"region": REGION_BICOL, "commodity": commodity_id})
    headers = _extract_headers(header_html)
    market_headers = headers[2:]
    price_html = _post(
        "tbl_price_get_comm_price.php",
        {"region": REGION_BICOL, "commodity": commodity_id, "count": str(len(market_headers))},
    )
    rows = _extract_rows(price_html, headers)
    return {"headers": headers, "rows": rows}


def _post(path: str, payload: dict[str, str]):
    data = urlencode(payload).encode("utf-8")
    request = Request(
        f"{BASE_URL}/{path}",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def _extract_headers(html: str):
    cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", html, flags=re.IGNORECASE | re.DOTALL)
    headers = [_clean_html(cell) for cell in cells]
    if len(headers) < 3:
        raise ValueError("Unexpected Bantay Presyo header format.")
    return headers


def _extract_rows(html: str, headers: list[str]):
    rows = {}
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL):
        cells = [
            _clean_html(cell)
            for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.IGNORECASE | re.DOTALL)
        ]
        if len(cells) != len(headers):
            continue
        row_data = {headers[idx]: cells[idx] for idx in range(len(headers))}
        commodity_name = row_data.get("COMMODITY", "").strip()
        if commodity_name:
            rows[commodity_name.lower()] = row_data
    return rows


def _clean_html(value: str):
    value = value.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    value = re.sub(r"<[^>]+>", "", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _parse_price(value: str):
    value = (value or "").strip()
    if not value or value.upper() == "N/A":
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _market_csv_exports_exist():
    return FILTERED_CSV_PATH.exists() and ML_CSV_PATH.exists()


def _build_export_row(target: TargetCommodity, row: dict[str, str], source_date: datetime, market_prices: dict[str, float], average_price: Decimal):
    month = source_date.month
    is_wet_season = 6 <= month <= 11
    return {
        "date": source_date.date().isoformat(),
        "year": source_date.year,
        "month": month,
        "region_id": REGION_BICOL,
        "commodity_id": target.commodity_id,
        "source_row_name": target.source_row,
        "crop_name": target.output_name,
        "ml_crop": _get_ml_crop_name(target.output_name),
        "specification": row.get("SPECIFICATIONS", ""),
        "legazpi_city_public_market": market_prices.get("LEGAZPI CITY PUBLIC MARKET", ""),
        "naga_peoples_mall": market_prices.get("NAGA PEOPLE'S MALL", ""),
        "market_count_used": len(market_prices),
        "average_price": float(average_price),
        "location": "Bicol",
        "source_markets": ", ".join(name for name in TARGET_MARKETS if name in market_prices),
        "rainfall_mm": 310.0 if is_wet_season else 72.0,
        "temperature_c": 27.0 if is_wet_season else 30.0,
        "humidity_pct": 81.0 if is_wet_season else 67.0,
        "soil_ph": 6.1,
        "yield_kg_ha": 3500.0,
    }


def _get_ml_crop_name(crop_name: str):
    ml_map = {
        "commercial milled rice": "Rice",
        "watermelon": "Watermelon",
        "melon": "Melon",
        "calamansi": "Calamansi",
        "ampalaya": "Ampalaya",
        "kalabasa": "Squash",
        "pechay": "Chinese Cabbage",
        "sitao": "String Beans",
        "talong": "Eggplant",
        "cabbage": "Cabbage",
        "garlic": "Garlic",
        "red onion": "Red Onion",
        "pipino": "Cucumber",
        "upo": "Bottle Gourd",
        "okra": "Okra",
        "lettuce": "Lettuce",
    }
    return ml_map.get(crop_name, crop_name.title())


def _write_market_csv_exports(export_rows: list[dict]):
    FILTERED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ML_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    filtered_fieldnames = [
        "date",
        "year",
        "month",
        "region_id",
        "commodity_id",
        "source_row_name",
        "crop_name",
        "ml_crop",
        "specification",
        "legazpi_city_public_market",
        "naga_peoples_mall",
        "market_count_used",
        "average_price",
        "location",
        "source_markets",
    ]
    with FILTERED_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as filtered_file:
        writer = csv.DictWriter(filtered_file, fieldnames=filtered_fieldnames)
        writer.writeheader()
        for row in export_rows:
            writer.writerow({field: row.get(field, "") for field in filtered_fieldnames})

    ml_fieldnames = [
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
    with ML_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as ml_file:
        writer = csv.DictWriter(ml_file, fieldnames=ml_fieldnames)
        writer.writeheader()
        for row in export_rows:
            writer.writerow(
                {
                    "date": row["date"],
                    "year": row["year"],
                    "month": row["month"],
                    "location": row["location"],
                    "crop": row["ml_crop"],
                    "rainfall_mm": row["rainfall_mm"],
                    "temperature_c": row["temperature_c"],
                    "humidity_pct": row["humidity_pct"],
                    "soil_ph": row["soil_ph"],
                    "yield_kg_ha": row["yield_kg_ha"],
                    "price_per_kg": row["average_price"],
                    "crop_name": row["crop_name"],
                    "legazpi_city_public_market": row["legazpi_city_public_market"],
                    "naga_peoples_mall": row["naga_peoples_mall"],
                    "market_count_used": row["market_count_used"],
                    "source_markets": row["source_markets"],
                    "source_row_name": row["source_row_name"],
                    "commodity_id": row["commodity_id"],
                }
            )
