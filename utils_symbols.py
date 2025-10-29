from __future__ import annotations
import csv
import re
from pathlib import Path
from typing import List, Set

_HK_RE_1 = re.compile(r"^(?:HK\.)?(\d{1,5})$", re.I)       # e.g. 700 / HK.700 / HK.00700
_HK_RE_2 = re.compile(r"^(\d{1,5})\.HK$", re.I)            # e.g. 700.HK
_US_RE_1 = re.compile(r"^(?:US\.)?([A-Z][A-Z0-9\-\.]{0,9})$", re.I)  # e.g. AAPL / US.AAPL
_US_RE_2 = re.compile(r"^([A-Z0-9\-\.]{1,10})\.US$", re.I)           # e.g. AAPL.US

def _canon_hk(num: str) -> str:
    return f"HK.{int(num):05d}"

def _canon_us(ticker: str) -> str:
    return f"US.{ticker.upper()}"

def normalize_symbol(raw: str) -> str:
    s = raw.strip()
    if not s:
        raise ValueError("empty symbol")

    m = _HK_RE_1.match(s)
    if m:
        return _canon_hk(m.group(1))
    m = _HK_RE_2.match(s)
    if m:
        return _canon_hk(m.group(1))

    m = _US_RE_1.match(s)
    if m:
        return _canon_us(m.group(1))
    m = _US_RE_2.match(s)
    if m:
        return _canon_us(m.group(1))

    # Accept already-canonical forms
    if s.upper().startswith(("HK.", "US.")):
        return s.upper()

    raise ValueError(f"Unsupported symbol format: {raw}")

def read_symbols(csv_path: str | Path) -> List[str]:
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"symbols csv not found: {p}")

    seen: Set[str] = set()
    out: List[str] = []
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "symbol" not in (reader.fieldnames or []):
            raise ValueError("CSV must have header 'symbol'")
        for row in reader:
            raw = (row.get("symbol") or "").strip()
            if not raw:
                continue
            try:
                canon = normalize_symbol(raw)
            except ValueError as e:
                # skip invalid rows but optionally log
                print(f"[symbols] skip invalid '{raw}': {e}")
                continue
            if canon not in seen:
                seen.add(canon)
                out.append(canon)
    if not out:
        raise ValueError("No valid symbols in CSV")
    return out
