"""
Udyam Setu — Normalisation Pipeline Tests
"""

import pytest
from app.services.normalisation import (
    normalize_business_name,
    normalize_address,
    normalize_pan,
    normalize_gstin,
    normalize_phone,
    normalize_record
)

# ─── 1. Business Name Tests ───────────────────────────────────────────────

def test_normalize_business_name():
    # 1. Standard Pvt Ltd
    res = normalize_business_name("Rajan Textiles Pvt Ltd")
    assert res["core_name"] == "rajan textiles"
    assert res["legal_suffix"] == "pvt ltd"
    assert res["normalized"] == "rajan textiles private limited"
    assert "rajan" in res["tokens"]
    
    # 2. Brackets
    res = normalize_business_name("Rajan Textiles (P) Ltd")
    assert res["legal_suffix"] == "(p) ltd"
    assert res["normalized"] == "rajan textiles private limited"
    
    # 3. Abbreviations Mfg
    res = normalize_business_name("Apex Mfg Pvt. Ltd.")
    assert res["core_name"] == "apex manufacturing"
    assert res["legal_suffix"] == "pvt. ltd."
    
    # 4. M/s prefix
    res = normalize_business_name("M/s Pioneer Engg LLP")
    assert res["core_name"] == "pioneer engineering"
    assert res["legal_suffix"] == "llp"
    
    # 5. Punctuation removal
    res = normalize_business_name("Global-Tech, Solutions Corp.")
    assert res["core_name"] == "global tech solutions"
    assert res["legal_suffix"] == "corp"
    
    # 6. Stopwords removal
    res = normalize_business_name("The Sunrise and Associates Ltd")
    assert "the" not in res["tokens"]
    assert "and" not in res["tokens"]
    assert "sunrise" in res["tokens"]
    
    # 7. No legal suffix
    res = normalize_business_name("Kaveri Foods")
    assert res["legal_suffix"] == ""
    assert res["normalized"] == "kaveri foods"
    
    # 8. Extra spaces
    res = normalize_business_name("  Namma   Enterprises  ")
    assert res["core_name"] == "namma enterprises"
    assert res["normalized"] == "namma enterprises"
    
    # 9. Empty string
    res = normalize_business_name("")
    assert res["normalized"] == ""
    
    # 10. Complex abbreviation
    res = normalize_business_name("Sri Venkateshwara Indl Corp")
    assert res["core_name"] == "venkateshwara industrial"
    assert res["legal_suffix"] == "corp"

# ─── 2. Address Tests ───────────────────────────────────────────────────

def test_normalize_address():
    # 1. Standard with comma
    res = normalize_address("Plot 42, Peenya Industrial Area", "560058")
    assert res["street"] == "plot 42"
    assert res["locality_normalized"] == "Peenya Industrial Area"
    assert res["pincode"] == "560058"
    assert res["district"] == "Bengaluru Urban"
    
    # 2. Known locality substitution (Electronic City)
    res = normalize_address("Phase 1, electronic city, Bangalore", "560100")
    assert res["locality_normalized"] == "Electronic City"
    
    # 3. Extract pincode from string
    res = normalize_address("Whitefield Main Road, Bengaluru 560066")
    assert res["pincode"] == "560066"
    assert res["locality_normalized"] == "Whitefield"
    
    # 4. No comma, heuristic split
    res = normalize_address("123 Laggere Main Road")
    assert res["street"] == "123"
    assert res["locality_normalized"] == "Laggere"
    
    # 5. Unknown pincode
    res = normalize_address("Mysore Road", "570001")
    assert res["district"] == "Unknown"
    
    # 6. Rural pincode
    res = normalize_address("Some Village", "562123")
    assert res["district"] == "Bengaluru Rural"
    
    # 7. Empty address
    res = normalize_address("")
    assert res["street"] == ""
    
    # 8. Messy punctuation
    res = normalize_address("No. 5., Bommanahalli..", "560068")
    assert res["street"] == "no 5"
    assert res["locality_normalized"] == "Bommanahalli"
    
    # 9. No numbers heuristic fallback
    res = normalize_address("Marathahalli Main Road")
    assert res["locality_normalized"] == "Marathahalli"
    
    # 10. Full normalized string format
    res = normalize_address("12, Peenya", "560058")
    assert res["full_normalized"] == "12 PEENYA INDUSTRIAL AREA BENGALURU URBAN 560058"

# ─── 3. PAN Tests ───────────────────────────────────────────────────────

def test_normalize_pan():
    # 1. Valid PAN
    assert normalize_pan("ABCDE1234F")["valid"] is True
    # 2. Valid Company PAN
    assert normalize_pan("ABCCA1234F")["checksum_ok"] is True
    # 3. Valid Individual PAN
    assert normalize_pan("ABCDP1234F")["checksum_ok"] is True
    # 4. Invalid length
    assert normalize_pan("ABCDE123F")["valid"] is False
    # 5. Invalid format (numbers first)
    assert normalize_pan("12345ABCDE")["valid"] is False
    # 6. Lowercase valid
    assert normalize_pan("abcde1234f")["normalized"] == "ABCDE1234F"
    # 7. Spaces and dashes
    assert normalize_pan("AB CDE-1234 F")["normalized"] == "ABCDE1234F"
    # 8. Empty
    assert normalize_pan("")["valid"] is False
    # 9. None
    assert normalize_pan(None)["valid"] is False
    # 10. Checksum fail (invalid 4th char)
    assert normalize_pan("ABCDX1234F")["valid"] is True
    assert normalize_pan("ABCDX1234F")["checksum_ok"] is False

# ─── 4. GSTIN Tests ─────────────────────────────────────────────────────

def test_normalize_gstin():
    # 1. Valid Karnataka GSTIN
    res = normalize_gstin("29ABCDE1234F1Z5")
    assert res["valid"] is True
    assert res["state_code"] == "29"
    assert res["pan_embedded"] == "ABCDE1234F"
    
    # 2. Lowercase and spaces
    res = normalize_gstin("29 abcde1234f 1z5")
    assert res["valid"] is True
    assert res["normalized"] == "29ABCDE1234F1Z5"
    
    # 3. Invalid length
    assert normalize_gstin("29ABCDE1234F1Z")["valid"] is False
    
    # 4. Invalid State Code (letters instead of digits)
    assert normalize_gstin("AAABCDE1234F1Z5")["valid"] is False
    
    # 5. Missing Z
    assert normalize_gstin("29ABCDE1234F1A5")["valid"] is False
    
    # 6. Empty
    assert normalize_gstin("")["valid"] is False
    
    # 7. None
    assert normalize_gstin(None)["valid"] is False
    
    # 8. Other state GSTIN (Valid)
    res = normalize_gstin("27ABCDE1234F1Z5") # Maharashtra
    assert res["valid"] is True
    assert res["state_code"] == "27"
    
    # 9. Invalid character in PAN part
    assert normalize_gstin("29ABCD11234F1Z5")["valid"] is False
    
    # 10. Exact regex boundary test
    assert normalize_gstin("29ABCDE1234F9Z9")["valid"] is True

# ─── 5. Phone Tests ─────────────────────────────────────────────────────

def test_normalize_phone():
    # 1. Valid 10 digit
    assert normalize_phone("9876543210") == "9876543210"
    # 2. +91 prefix
    assert normalize_phone("+919876543210") == "9876543210"
    # 3. +91 with space
    assert normalize_phone("+91 9876543210") == "9876543210"
    # 4. 0 prefix
    assert normalize_phone("09876543210") == "9876543210"
    # 5. Dashes
    assert normalize_phone("987-654-3210") == "9876543210"
    # 6. Brackets
    assert normalize_phone("(987) 654 3210") == "9876543210"
    # 7. Invalid length
    assert normalize_phone("98765") is None
    # 8. Letters included
    assert normalize_phone("98765ABCDE") is None
    # 9. Empty
    assert normalize_phone("") is None
    # 10. None
    assert normalize_phone(None) is None

# ─── 6. Master Record Tests ─────────────────────────────────────────────

def test_normalize_record():
    raw_record = {
        "business_name": "M/s Rajan Textiles Pvt Ltd",
        "address_raw": "123, Peenya, Bengaluru 560058",
        "pan": " ABCDE1234C ",
        "gstin": "29ABCDE1234C1Z5",
        "phone": "+91 9999988888"
    }
    
    norm = normalize_record(raw_record)
    
    # 1-5. Checks for Master function aggregations
    assert norm["business_name_normalized"] == "rajan textiles private limited"
    assert norm["address_locality"] == "Peenya Industrial Area"
    assert norm["pan"] == "ABCDE1234C"
    assert norm["gstin"] == "29ABCDE1234C1Z5"
    assert norm["phone"] == "9999988888"
    
    # 6. Missing PAN fallback to GSTIN
    raw_record_no_pan = raw_record.copy()
    del raw_record_no_pan["pan"]
    norm2 = normalize_record(raw_record_no_pan)
    assert norm2["pan"] == "ABCDE1234C" # Extracted from GSTIN
    
    # 7. Missing GSTIN doesn't overwrite valid PAN
    raw_record_no_gstin = raw_record.copy()
    raw_record_no_gstin["gstin"] = "INVALID"
    norm3 = normalize_record(raw_record_no_gstin)
    assert norm3["pan"] == "ABCDE1234C"
    assert norm3["gstin"] is None
    
    # 8. Soundex exists
    assert "soundex" in norm
    assert len(norm["soundex"]) > 0
    
    # 9. Metaphone exists
    assert "metaphone" in norm
    assert len(norm["metaphone"]) > 0
    
    # 10. Tokens exist
    assert "rajan" in norm["business_name_tokens"]
