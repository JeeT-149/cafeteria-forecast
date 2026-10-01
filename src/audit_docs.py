import os
import re
import csv

approved_numbers = {
    "5,961,005", "17,115", "5,943,890", "438", "508,357", "5,435,095", "96,199", "5,338,896", 
    "2,178,801", "2,095,347", "7,426,133", "5,960,826", "1,397", "1,218", "14,765", "17,219", 
    "2,354", "2,589", "12,848", "4,084", "1,538", "3,336", "12,209", "14,461", "2,389", "2,559", 
    "110", "142", "788,361", "67", "902", "13", "9,752", "9,314", "8,590", "6,928", "2,807", 
    "9,119", "8,790", "8,489", "6,969", "1,010", "2,480,228", "2,344,842", "653,115", "443,902", 
    "38,477", "432", "8", "1", "18", "147", "11,622", "377", "545,041",
    "95,711", "95,709", "96,169", "230", "34", "0", 
    "450,280", "145,978", "94,209", "91,986", "42,854", "5,701",
    "9914", "9454", "10374", "9632", "9172", "10092", "9363", "8902", "9824", "7530", "7070", "7990", 
    "655", "194", "1116", "200", "660", "8666", "8206", "9126",
    "11,034,801,932", "13,517,179", "365", "80", "51", "39", "22"
}

def verify_csv_math():
    try:
        assert 5961005 - 17115 == 5943890, "Math error 1"
        assert 5943890 - 438 - 508357 == 5435095, "Math error 2"
        assert 5435095 - 96199 == 5338896, "Math error 3"
        print("PASS: Basic math verifies.")
        
        csv_valid_total = 0
        b2_valid = 0
        b1_valid = 0
        
        with open("data/processed/sales_daily_branch.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                val = int(row['valid_paid_orders'])
                branch = int(row['branch_id'])
                csv_valid_total += val
                if branch == 2:
                    b2_valid += val
                if branch == 1:
                    b1_valid += val
        
        assert csv_valid_total == 5338896, f"CSV valid total mismatch: {csv_valid_total}"
        assert b2_valid == 2178801, f"Branch 2 valid mismatch: {b2_valid}"
        assert b1_valid == 2095347, f"Branch 1 valid mismatch: {b1_valid}"
        assert 1 + 429 + 8 == 438, "Math error 4"
        print("PASS: CSV totals verify.")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False

def audit_docs():
    docs_dir = "docs"
    files = [f for f in os.listdir(docs_dir) if f.endswith(".md")]
    
    issues = []
    
    for file in files:
        with open(os.path.join(docs_dir, file), 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find integers with optional commas
            matches = re.finditer(r'(?<!\.)\b([1-9]\d{0,2}(?:,\d{3})+|\d{2,})\b(?!\.)', content)
            for match in matches:
                num = match.group(1)
                
                # Exclude years and dates (e.g. 2024, 2025) and simple IDs
                if num in {"2024", "2025", "11", "13", "14", "16", "17", "18", "10", "-1"}:
                    continue
                # Exclude smaller than 100 which are likely branches/indices unless in approved
                if len(num) <= 2 and num not in approved_numbers and "," not in num:
                    continue
                
                # Check if it's approved
                if num not in approved_numbers and num.replace(",", "") not in approved_numbers:
                    issues.append((file, num))

    if issues:
        print("REVIEW items:")
        for file, num in set(issues):
            print(f"- {file}: {num}")
    else:
        print("No unverified large numbers found in docs.")

if __name__ == "__main__":
    verify_csv_math()
    audit_docs()