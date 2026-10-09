"""Cross-check independently sourced listing name against Finnhub profile.

Conservative name comparison: a mismatch blocks promotion; a match is not
independent verification of legal identity or corporate actions.
"""
import re
from difflib import SequenceMatcher

LEGAL = {"inc","incorporated","corp","corporation","co","company","ltd","limited",
         "plc","holdings","holding","the","class","common","stock","shares",
         "ordinary","american","depositary","adr","ads"}
def _tokens(value):
    value = re.split(r"\s+-\s+(?:class|common|ordinary|american depositary)",value,flags=re.I)[0]
    return [w for w in re.findall(r"[a-z0-9]+",value.lower()) if w not in LEGAL]

def identity_check(listing_symbol, listing_name, profile):
    result = {"status":"IDENTITY_UNVERIFIED","listing_symbol":listing_symbol,
              "listing_name":listing_name,"profile_symbol":None,"profile_name":None,
              "name_similarity":None,"issuer_identity_verified":False,
              "reason":"Profile unavailable or unverified"}
    if profile.get("status") != "PROFILE_RESEARCH_AVAILABLE":
        result["reason"]="Profile not available; cannot compare issuer identity"
        return result
    result["profile_symbol"]=profile.get("profile_symbol")
    result["profile_name"]=profile.get("issuer_name")
    if profile.get("profile_symbol") != listing_symbol:
        result.update(status="IDENTITY_MISMATCH",reason="Profile ticker differs from listing ticker")
        return result
    a,b=_tokens(listing_name or ""),_tokens(profile.get("issuer_name") or "")
    if not a or not b:
        result["reason"]="Issuer name missing after normalization"
        return result
    similarity=SequenceMatcher(None," ".join(a)," ".join(b)).ratio()
    result["name_similarity"]=round(similarity,3)
    overlap=len(set(a)&set(b))/max(1,min(len(set(a)),len(set(b))))
    if similarity < .72 or overlap < .5:
        result.update(status="IDENTITY_MISMATCH",reason="Listing name and profile issuer name disagree; investigate symbol reuse/provider mapping")
    else:
        result.update(status="NAME_CONSISTENT_UNVERIFIED",reason="Names consistent, but legal issuer identity not independently verified")
    return result

