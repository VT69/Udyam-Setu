"""
Udyam Setu — Data Normalisation Pipeline
Focuses on Karnataka business records and standard entity resolution preprocessing.
"""

import re
import string
import jellyfish

# ─── Reference Data & Dictionaries ──────────────────────────────────────────

ABBREVIATIONS = {
    r"\bpvt\b": "private",
    r"\bp ltd\b": "private limited",
    r"\bmfg\b": "manufacturing",
    r"\bindl\b": "industrial",
    r"\bengg\b": "engineering",
    r"\bbros\b": "brothers",
    r"\bco\b": "company",
    r"\bcorp\b": "corporation",
    r"\bassoc\b": "associates",
    r"\bintl\b": "international",
    r"\bnatl\b": "national",
    r"\bent\b": "enterprises",
    r"\bm/s\b": "",
}

LEGAL_SUFFIXES = [
    r"private limited",
    r"pvt ltd",
    r"\(p\) ltd",
    r"pvt\. ltd\.",
    r"pvt\. ltd",
    r"llp",
    r"ltd",
    r"limited",
    r"inc",
    r"corp",
    r"corporation",
    r"industries",
    r"enterprises",
]
SUFFIX_PATTERN = re.compile(r'\b(' + '|'.join(LEGAL_SUFFIXES) + r')\b\.?$', re.IGNORECASE)

STOPWORDS = {"the", "and", "of", "in", "a", "an", "m/s", "shree", "sri"}

KARNATAKA_LOCALITIES = {
    "peenya": "Peenya Industrial Area",
    "whitefield": "Whitefield",
    "marathahalli": "Marathahalli",
    "electronic city": "Electronic City",
    "bommanahalli": "Bommanahalli",
    "yelahanka": "Yelahanka",
    "laggere": "Laggere",
    "hegganahalli": "Hegganahalli",
    "chokkasandra": "Chokkasandra",
    "veerasandra": "Veerasandra",
    "bommasandra": "Bommasandra Industrial Area",
}

# Simplified mapping for Bengaluru Urban pincodes (560xxx)
def get_district_from_pincode(pincode: str) -> str:
    if pincode and pincode.startswith("560"):
        return "Bengaluru Urban"
    elif pincode and pincode.startswith("562"):
        return "Bengaluru Rural"
    return "Unknown"


# ─── Normalisation Functions ───────────────────────────────────────────────

def normalize_business_name(raw_name: str) -> dict:
    if not raw_name:
        return {"normalized": "", "legal_suffix": "", "core_name": "", "soundex": "", "metaphone": "", "tokens": []}
    
    # Lowercase and handle punctuation
    name_norm = raw_name.lower().strip()
    
    # Extract legal suffix
    match = SUFFIX_PATTERN.search(name_norm)
    legal_suffix = match.group(1).strip() if match else ""
    core_name = SUFFIX_PATTERN.sub("", name_norm).strip()
    
    # Remove all punctuation except spaces
    core_name = core_name.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    core_name = re.sub(r'\s+', ' ', core_name).strip()
    
    # Expand abbreviations
    for pattern, replacement in ABBREVIATIONS.items():
        core_name = re.sub(pattern, replacement, core_name)
    
    core_name = re.sub(r'\s+', ' ', core_name).strip()
    
    # Tokens
    tokens = [t for t in core_name.split() if t not in STOPWORDS and len(t) > 1]
    
    # Re-assemble normalized string (including standardized legal suffix if present)
    standard_suffix = legal_suffix.replace(".", "").replace("pvt ltd", "private limited").replace("(p) ltd", "private limited")
    normalized_full = f"{core_name} {standard_suffix}".strip()
    
    return {
        "normalized": normalized_full,
        "legal_suffix": legal_suffix,
        "core_name": core_name,
        "soundex": jellyfish.soundex(core_name) if core_name else "",
        "metaphone": jellyfish.metaphone(core_name) if core_name else "",
        "tokens": tokens
    }


def normalize_address(raw_address: str, pincode: str = None) -> dict:
    if not raw_address:
        return {"street": "", "locality": "", "locality_normalized": "", "pincode": pincode or "", "district": "", "full_normalized": ""}
    
    addr_lower = raw_address.lower().replace(",", " ").replace(".", " ")
    addr_lower = re.sub(r'\s+', ' ', addr_lower).strip()
    
    # Extract pincode if not provided
    extracted_pincode = pincode
    if not extracted_pincode:
        pin_match = re.search(r'\b(560\d{3}|562\d{3})\b', addr_lower)
        if pin_match:
            extracted_pincode = pin_match.group(1)
            
    # Simple address parser: split roughly by numbers/door vs area
    # In a real system, this would be a CRFs or Spacy model.
    street = ""
    locality = ""
    
    parts = raw_address.split(',')
    if len(parts) >= 2:
        street = parts[0].strip()
        locality = parts[1].strip()
    else:
        # If no commas, assume first word with numbers is street, rest is locality
        words = addr_lower.split()
        if len(words) > 0 and any(char.isdigit() for char in words[0]):
            street = words[0]
            locality = " ".join(words[1:])
        else:
            locality = raw_address
            
    # Normalize locality against Karnataka master list
    locality_normalized = locality
    for key, value in KARNATAKA_LOCALITIES.items():
        if key in locality.lower():
            locality_normalized = value
            break
            
    district = get_district_from_pincode(extracted_pincode)
    
    full_norm = f"{street} {locality_normalized} {district} {extracted_pincode}".strip()
    full_norm = re.sub(r'\s+', ' ', full_norm)
    
    return {
        "street": street,
        "locality": locality,
        "locality_normalized": locality_normalized,
        "pincode": extracted_pincode or "",
        "district": district,
        "full_normalized": full_norm.upper()
    }


def normalize_pan(pan: str) -> dict:
    if not pan:
        return {"valid": False, "normalized": "", "checksum_ok": False}
    
    # Strip spaces and uppercase
    pan_norm = str(pan).upper().replace(" ", "").replace("-", "")
    
    # Format: 5 letters, 4 numbers, 1 letter
    is_valid = bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan_norm))
    
    # Basic checksum validation (4th char is status, e.g., C for company, P for individual)
    checksum_ok = False
    if is_valid:
        status_char = pan_norm[3]
        if status_char in ['C', 'P', 'H', 'F', 'A', 'T', 'B', 'L', 'J', 'G']:
            checksum_ok = True
            
    return {
        "valid": is_valid,
        "normalized": pan_norm if is_valid else pan,
        "checksum_ok": checksum_ok
    }


def normalize_gstin(gstin: str) -> dict:
    if not gstin:
        return {"valid": False, "normalized": "", "state_code": "", "pan_embedded": ""}
        
    gstin_norm = str(gstin).upper().replace(" ", "").replace("-", "")
    
    # Format: 2 digits (state), 10 char PAN, 1 entity num, 1 Z, 1 checksum
    is_valid = bool(re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gstin_norm))
    
    state_code = ""
    pan_embedded = ""
    
    if len(gstin_norm) == 15:
        state_code = gstin_norm[0:2]
        pan_embedded = gstin_norm[2:12]
        
    return {
        "valid": is_valid,
        "normalized": gstin_norm if is_valid else gstin,
        "state_code": state_code,
        "pan_embedded": pan_embedded
    }


def normalize_phone(phone: str) -> str:
    if not phone:
        return None
        
    # Strip +91, 0 prefix, spaces, dashes, brackets
    phone_str = str(phone)
    if phone_str.startswith("+91"):
        phone_str = phone_str[3:]
    elif phone_str.startswith("0") and len(phone_str) > 10:
        phone_str = phone_str[1:]
        
    phone_clean = re.sub(r'[\s\-\(\)\.]', '', phone_str)
    
    # Check if exactly 10 digits
    if len(phone_clean) == 10 and phone_clean.isdigit():
        return phone_clean
    return None


def normalize_record(record: dict) -> dict:
    """Master function applying all normalizations to a raw record dictionary."""
    normalized = record.copy()
    
    name_res = normalize_business_name(record.get("business_name", ""))
    normalized["business_name_normalized"] = name_res["normalized"]
    normalized["business_name_tokens"] = name_res["tokens"]
    normalized["soundex"] = name_res["soundex"]
    normalized["metaphone"] = name_res["metaphone"]
    
    addr_res = normalize_address(record.get("address_raw", ""), record.get("address_pincode", ""))
    normalized["address_street"] = addr_res["street"]
    normalized["address_locality"] = addr_res["locality_normalized"]
    normalized["address_pincode"] = addr_res["pincode"]
    normalized["address_district"] = addr_res["district"]
    normalized["address_full_normalized"] = addr_res["full_normalized"]
    
    pan_res = normalize_pan(record.get("pan", ""))
    normalized["pan"] = pan_res["normalized"] if pan_res["valid"] else None
    
    gstin_res = normalize_gstin(record.get("gstin", ""))
    normalized["gstin"] = gstin_res["normalized"] if gstin_res["valid"] else None
    
    normalized["phone"] = normalize_phone(record.get("phone", ""))
    
    # Ensure PAN from GSTIN if missing
    if not normalized["pan"] and gstin_res["valid"]:
        normalized["pan"] = gstin_res["pan_embedded"]
        
    return normalized
