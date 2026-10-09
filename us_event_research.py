"""Public SEC filing signals for research triage, not a complete event calendar."""
import json
from html.parser import HTMLParser
import os
import re
import urllib.request
from datetime import date, timedelta

def sec_headers():
    """Do not make SEC requests with invented or undeclared contact details."""
    contact = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", contact):
        raise RuntimeError("SEC_CONTACT_EMAIL_NOT_CONFIGURED")
    return {"User-Agent": "Dipsaus Research Scanner " + contact,
            "Accept": "application/json"}
FORMS = {"8-K", "8-K/A", "10-Q", "10-K", "S-1", "S-3", "424B5", "6-K", "20-F", "SC 13D", "SC 13G", "DEF 14A"}

def _json(url):
    request = urllib.request.Request(url, headers=sec_headers())
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def ticker_ciks():
    raw = _json("https://www.sec.gov/files/company_tickers.json")
    return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in raw.values()}

class _FilingText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def filing_content_review(filing):
    """Bounded filing excerpt; no LLM interpretation, no automatic risk clearance."""
    result = {"status":"NOT_FETCHED","excerpt":None,"item_codes":filing.get("item_codes",[]),
              "source_url":filing.get("url"),"content_verified":False,
              "event_risk_cleared":False,"substantive_sections":[],"substantive_review_status":"NOT_ASSESSED"}
    url = filing.get("url","")
    if not re.fullmatch(r"https://www\.sec\.gov/Archives/edgar/data/[0-9]+/[0-9]+/[A-Za-z0-9_.-]+",url):
        result["status"]="INVALID_SEC_ARCHIVE_URL"
        return result
    try:
        request = urllib.request.Request(url,headers=sec_headers())
        with urllib.request.urlopen(request,timeout=15) as response:
            raw=response.read(500001)
        if len(raw)>500000:
            result["status"]="DOCUMENT_TOO_LARGE_FOR_BOUNDED_REVIEW"
            return result
        parser=_FilingText()
        parser.feed(raw.decode("utf-8",errors="replace"))
        clean=re.sub(r"\s+"," "," ".join(parser.parts)).strip()
        if len(clean)<100:
            result["status"]="INSUFFICIENT_EXTRACTED_TEXT"
            return result
        result["excerpt"]=clean[:2200]
        # Match item headings, not the SEC cover page or checkboxes.
        # These are excerpts for manual inspection, not an interpretation.
        headings=list(re.finditer(r"(?i)\bItem\s+([1-9]\.[0-9]{2})\s*[.:-]?\s*",clean))
        sections=[]
        for i,match in enumerate(headings):
            end=headings[i+1].start() if i+1<len(headings) else len(clean)
            body=clean[match.end():end].strip()
            if len(body)<40:
                continue
            sections.append({"item_code":match.group(1),"excerpt":body[:3500],
                             "truncated":len(body)>3500})
        result["substantive_sections"]=sections[:8]
        result["substantive_review_status"]="ITEM_EXCERPTS_REQUIRE_HUMAN_REVIEW" if sections else "NO_SUBSTANTIVE_ITEM_TEXT_FOUND"
        result["status"]="EXCERPT_REQUIRES_HUMAN_REVIEW"
    except Exception as exc:
        result["status"]="FETCH_FAILED: "+type(exc).__name__
    return result

def filing_review(symbol, ciks, today=None):
    """Fail closed: absence of filings NEVER means events are clear."""
    result = {"source": "SEC EDGAR recent submissions", "status": "UNVERIFIED",
              "earnings_calendar_verified": False, "non_sec_events_verified": False,
              "company_event_risk_verified": False, "corporate_actions_verified": False,
              "recent_material_filing_signals": [], "reason": None}
    cik = ciks.get(symbol.upper())
    if not cik:
        result.update(status="NO_SEC_TICKER_MATCH", reason="Ticker missing from SEC map; ADR/foreign or listing mismatch possible")
        return result
    try:
        data = _json("https://data.sec.gov/submissions/CIK" + cik + ".json")
        recent = data.get("filings", {}).get("recent", {})
        cutoff = (today or date.today()) - timedelta(days=30)
        for form, filed, accession, doc, items in zip(recent.get("form", []), recent.get("filingDate", []),
                                               recent.get("accessionNumber", []), recent.get("primaryDocument", []), recent.get("items", [])):
            if form in FORMS and filed >= cutoff.isoformat():
                result["recent_material_filing_signals"].append({
                    "form": form, "filed": filed, "item_codes": [x.strip() for x in str(items or "").split(",") if x.strip()],
                    "url": "https://www.sec.gov/Archives/edgar/data/" + str(int(cik)) + "/" + accession.replace("-", "") + "/" + doc})
        result["status"] = "FILING_REVIEW_REQUIRED" if result["recent_material_filing_signals"] else "NO_RECENT_MATCHING_SEC_FILINGS"
        result["reason"] = "Read filings and verify earnings, corporate actions and non-SEC events manually; SEC signals alone cannot clear event risk"
    except Exception as exc:
        result.update(status="SEC_FETCH_FAILED", reason=type(exc).__name__)
    return result

