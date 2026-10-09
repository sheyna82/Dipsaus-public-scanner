"""Conservative issuer-specific headline triage; never event clearance."""
import re
STOP={"inc","incorporated","corp","corporation","company","co","ltd","limited","plc","holdings","holding","the","international","systems","technologies","technology","group","class","common","stock"}
def issuer_terms(name):
    return [x for x in re.findall(r"[a-z0-9]+",(name or "").lower()) if x not in STOP and len(x)>2]
def classify_headlines(news,profile):
    terms=issuer_terms(profile.get("issuer_name"))
    result={"status":"RELEVANCE_UNVERIFIED","issuer_terms":terms,
            "issuer_specific":[],"not_issuer_specific":[],"unresolved":[],
            "event_risk_cleared":False}
    if not terms or profile.get("status")!="PROFILE_RESEARCH_AVAILABLE":
        result["unresolved"]=news.get("flagged_headline_review",[])
        return result
    for item in news.get("flagged_headline_review",[]):
        title=item.get("headline","").lower()
        matches=[term for term in terms if re.search(r"(?<![a-z0-9])"+re.escape(term)+r"(?![a-z0-9])",title)]
        enriched={**item,"matched_issuer_terms":matches}
        if matches:
            result["issuer_specific"].append(enriched)
        elif re.search(r"\b(stocks|portfolio|market|sector|etfs|dividend aristocrats)\b",title):
            result["not_issuer_specific"].append(enriched)
        else:
            result["unresolved"].append(enriched)
    result["status"]="HEURISTIC_TRIAGE_REVIEW_REQUIRED"
    return result

# Specific actions only; broad words such as earnings, results, dividend and
# guidance alone are not proof of a new issuer event.
EVENT_PATTERNS=(
    r"\bannounc(?:es|ed)\b.{0,90}\b(?:restructur|acqui|merg|offering|buyback|dividend|layoff|strategic review|strategic alternatives)",
    r"\b(?:files|filed|launches|launched|completes|completed|approves|approved|declares|declared|suspends|suspended|cuts|cut|raises|raised)\b.{0,90}\b(?:offering|bankruptcy|merger|acquisition|dividend|guidance|buyback|restructur|capital raise)",
    r"\b(?:strategic review|special committee|strategic alternatives|going concern|reverse stock split|reverse split|trading halt|delisting|restatement|bankruptcy|recall|fda approval)\b",
)
ANALYSIS_PATTERNS=(
    r"\b(?:analyst|valuation|price target|stock has been|since last earnings|can it rebound|is it a buy|should you buy|worth buying|forecast|outlook for|shares (?:fell|rose|drop|jump))\b",
)
def classify_event_materiality(relevance):
    """Headline-only priority, not verified event occurrence or materiality."""
    result={"status":"HEADLINE_ONLY_REVIEW_REQUIRED","potential_concrete_events":[],
            "analysis_or_commentary":[],"ambiguous_issuer_news":[],
            "not_issuer_specific":relevance.get("not_issuer_specific",[]),
            "unresolved_relevance":relevance.get("unresolved",[]),
            "event_risk_cleared":False,"event_occurrence_verified":False}
    for item in relevance.get("issuer_specific",[]):
        title=item.get("headline","").lower()
        if any(re.search(p,title) for p in EVENT_PATTERNS):
            result["potential_concrete_events"].append(item)
        elif any(re.search(p,title) for p in ANALYSIS_PATTERNS):
            result["analysis_or_commentary"].append(item)
        else:
            result["ambiguous_issuer_news"].append(item)
    return result

