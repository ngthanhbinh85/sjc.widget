#!/usr/bin/env python3

import json
import re
import sys
import xml.etree.ElementTree as ET
from html import unescape

try:
    from curl_cffi import requests
except ImportError:
    print(
        json.dumps(
            {
                "error": (
                    "Chưa cài curl_cffi. Chạy: "
                    "python3 -m pip install --upgrade curl_cffi"
                ),
                "buy": None,
                "sell": None,
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


API_URL = "https://sjc.com.vn/GoldPrice/Services/PriceService.ashx"
PAGE_URL = "https://sjc.com.vn/gia-vang-online"
SPOT_URL = "https://xaus.com/api/v1/spot"
VCB_URL = (
    "https://portal.vietcombank.com.vn/"
    "Usercontrols/TVPortal.TyGia/pXML.aspx"
)

SESSION = requests.Session()

BROWSER_HEADERS = {
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def normalize_number(value):
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        number = int(value)
    else:
        text = re.sub(r"[^\d]", "", str(value))

        if not text:
            return None

        number = int(text)

    # SJC đôi khi trả giá theo nghìn đồng.
    if 10_000 <= number < 1_000_000:
        number *= 1000

    return number


def walk_json(value):
    if isinstance(value, dict):
        lowered = {
            str(key).strip().lower(): item
            for key, item in value.items()
        }

        name = (
            lowered.get("typename")
            or lowered.get("type_name")
            or lowered.get("name")
            or lowered.get("type")
            or lowered.get("goldtype")
            or lowered.get("gold_type")
            or lowered.get("productname")
            or lowered.get("product_name")
            or ""
        )

        buy = (
            lowered.get("buy")
            or lowered.get("buyvalue")
            or lowered.get("buy_value")
            or lowered.get("buyprice")
            or lowered.get("buy_price")
        )

        sell = (
            lowered.get("sell")
            or lowered.get("sellvalue")
            or lowered.get("sell_value")
            or lowered.get("sellprice")
            or lowered.get("sell_price")
        )

        normalized_buy = normalize_number(buy)
        normalized_sell = normalize_number(sell)

        if normalized_buy is not None and normalized_sell is not None:
            yield {
                "name": str(name).strip(),
                "buy": normalized_buy,
                "sell": normalized_sell,
            }

        for child in value.values():
            yield from walk_json(child)

    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def select_sjc_bar(items):
    valid_items = [
        item
        for item in items
        if item.get("buy")
        and item.get("sell")
    ]

    preferred_keywords = [
        "sjc 1l",
        "1l, 10l",
        "1l 10l",
        "10l",
        "1kg",
        "vàng sjc",
        "vang sjc",
        "vàng miếng",
        "vang mieng",
    ]

    for keyword in preferred_keywords:
        for item in valid_items:
            if keyword in item.get("name", "").lower():
                return item

    return valid_items[0] if valid_items else None


def parse_api(body):
    text = body.strip().lstrip("\ufeff")

    if not text:
        raise ValueError("API trả về nội dung rỗng")

    if text[0] not in "[{":
        raise ValueError("API trả HTML hoặc dữ liệu không phải JSON")

    data = json.loads(text)

    # Kiểu phản hồi ASP.NET đôi khi bọc trong thuộc tính d.
    if isinstance(data, dict) and "d" in data:
        data = data["d"]

    if isinstance(data, str):
        stripped = data.strip()

        if stripped.startswith("{") or stripped.startswith("["):
            data = json.loads(stripped)

    items = list(walk_json(data))
    selected = select_sjc_bar(items)

    if selected is None:
        raise ValueError("Không tìm thấy giá mua và giá bán trong JSON")

    selected["source"] = "PriceService.ashx"
    selected["fallback"] = False

    return selected


def html_to_text(body):
    text = unescape(body)

    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_page(body):
    text = html_to_text(body)

    patterns = [
        (
            "Vàng SJC 1L, 10L, 1KG",
            (
                r"Vàng\s+SJC\s+1L[\s,;/\-]*10L[\s,;/\-]*1KG"
                r"[^0-9]{0,250}"
                r"([\d.,]{5,})"
                r"[^0-9]{1,120}"
                r"([\d.,]{5,})"
            ),
        ),
        (
            "Vàng SJC 1L, 10L, 1KG",
            (
                r"SJC\s+1L[\s,;/\-]*10L[\s,;/\-]*1KG"
                r"[^0-9]{0,250}"
                r"([\d.,]{5,})"
                r"[^0-9]{1,120}"
                r"([\d.,]{5,})"
            ),
        ),
        (
            "Vàng miếng SJC",
            (
                r"Vàng\s+miếng\s+SJC"
                r"[^0-9]{0,250}"
                r"([\d.,]{5,})"
                r"[^0-9]{1,120}"
                r"([\d.,]{5,})"
            ),
        ),
    ]

    for product_name, pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if not match:
            continue

        buy = normalize_number(match.group(1))
        sell = normalize_number(match.group(2))

        if buy and sell:
            return {
                "name": product_name,
                "buy": buy,
                "sell": sell,
                "source": "gia-vang-online",
                "fallback": True,
            }

    raise ValueError("Không tìm thấy giá SJC trong nội dung trang")


def browser_get(url, headers=None):
    merged_headers = BROWSER_HEADERS.copy()

    if headers:
        merged_headers.update(headers)

    response = SESSION.get(
        url,
        headers=merged_headers,
        impersonate="chrome",
        timeout=20,
        allow_redirects=True,
    )

    response.raise_for_status()
    return response


def parse_vcb_usd_sell(body):
    root = ET.fromstring(body.strip().lstrip("\ufeff"))

    for item in root.iter():
        attrs = {
            str(key).lower(): value
            for key, value in item.attrib.items()
        }

        code = attrs.get("currencycode", "").upper()
        if code != "USD":
            continue

        value = attrs.get("sell")
        if not value:
            break

        rate = float(value.replace(",", ""))
        if rate > 0:
            return rate

    raise ValueError("Không tìm thấy tỷ giá bán USD")


def add_international_data(result):
    market_errors = []
    spot = None
    usd_vnd = None

    try:
        response = browser_get(
            SPOT_URL,
            {"Accept": "application/json"},
        )
        payload = response.json()
        spot = float(payload["spot_usd_oz"])
    except Exception as error:
        market_errors.append(f"XAU/USD: {error}")

    try:
        response = browser_get(
            VCB_URL,
            {"Accept": "application/xml,text/xml,*/*"},
        )
        usd_vnd = parse_vcb_usd_sell(response.text)
    except Exception as error:
        market_errors.append(f"USD/VND: {error}")

    international = None
    premium = None

    if spot is not None and usd_vnd is not None:
        international = spot * usd_vnd * 37.5 / 31.1034768
        sell = result.get("sell")
        if sell is not None:
            premium = float(sell) - international

    result.update(
        {
            "spot_usd_oz": spot,
            "usd_vnd_sell": usd_vnd,
            "international_vnd_luong": international,
            "premium_sell": premium,
            "market_error": " | ".join(market_errors) or None,
        }
    )

    return result


def main():
    errors = []
    page_body = None

    # Mở trang chính trước để tạo phiên và nhận cookie.
    try:
        response = browser_get(
            PAGE_URL,
            {
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/avif,"
                    "image/webp,*/*;q=0.8"
                ),
            },
        )

        page_body = response.text

    except Exception as error:
        errors.append(f"Trang chính: {error}")

    # Gọi endpoint sau khi đã có cookie.
    try:
        response = browser_get(
            API_URL,
            {
                "Accept": (
                    "application/json, text/javascript, "
                    "*/*; q=0.01"
                ),
                "Referer": PAGE_URL,
                "Origin": "https://sjc.com.vn",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

        result = add_international_data(parse_api(response.text))

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return

    except Exception as error:
        errors.append(f"API: {error}")

    # Fallback: đọc nội dung trang chính.
    try:
        if not page_body:
            page_body = browser_get(PAGE_URL).text

        result = add_international_data(parse_page(page_body))

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return

    except Exception as error:
        errors.append(f"Đọc trang: {error}")

    print(
        json.dumps(
            {
                "error": " | ".join(errors),
                "buy": None,
                "sell": None,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )

    sys.exit(1)


if __name__ == "__main__":
    main()
