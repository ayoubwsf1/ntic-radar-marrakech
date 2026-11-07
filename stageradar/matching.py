from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

import pandas as pd

from .mail_parser import Parsed
from .text_utils import norm

GENERIC_NAMES = {"marketing agency", "la boite", "billboard", "omd", "spikal", "quick agency", "wellbek", "push"}


def domain_of(site: str) -> str:
    host = urlparse(site if "//" in site else f"//{site}").netloc.lower().split(":")[0]
    return re.sub(r"^(www|en|fr|ar)\.", "", host)


def build_index(df: pd.DataFrame) -> list[dict]:
    idx = []
    for _, r in df.iterrows():
        name_n = norm(r["nom"]).replace(" - social media agency", "").strip()
        idx.append({
            "id": int(r["id"]), "nom": r["nom"], "domain": domain_of(r["site"] or ""),
            "name_n": name_n, "generic": name_n in GENERIC_NAMES or len(name_n) < 5,
            "name_rx": re.compile(r"(?<![a-z0-9])" + re.escape(name_n) + r"(?![a-z0-9])"),
        })
    return idx


def _addr_domain_match(addrs: list, domain: str) -> Optional[str]:
    if not domain:
        return None
    for a in addrs:
        d = a.rsplit("@", 1)[-1]
        if d == domain or d.endswith("." + domain):
            return a
    return None


def match_agence(index: list[dict], p: Parsed, sent: bool) -> Optional[dict]:
    addrs = p.to_addrs if sent else p.from_addrs
    for ag in index:
        if _addr_domain_match(addrs, ag["domain"]):
            return ag

    if sent:
        return None

    hay_head = norm(f"{p.from_name} {p.subject}")
    hay_body = norm(p.body[:1500])
    for ag in index:
        if ag["generic"]:
            continue
        if ag["name_rx"].search(hay_head) or ag["name_rx"].search(hay_body):
            return ag
    return None
