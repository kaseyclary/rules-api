import json
import os
from glob import glob

def update_agency_ids(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Handle word_counts files
    if "agencies" in data:
        for agency in data["agencies"]:
            if "Engineering and Land Surveying Examining Board" in agency.get("agency", ""):
                agency["agency_id"] = "193.3"
                # Update nested chapters
                for chapter in agency.get("chapters", []):
                    if "Engineering and Land Surveying Examining Board" in chapter.get("agency", ""):
                        chapter["agency_id"] = "193.3"
    
    # Handle nested rules files
    else:
        for agency in data.get("agencies", []):
            if "Engineering and Land Surveying Examining Board" in agency.get("agencyName", ""):
                agency["agencyId"] = "193.3"
    
    # Write the updated data back to the file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    # Update word_counts files
    word_counts_path = "src/data/rules/word_counts"
    word_count_files = glob(os.path.join(word_counts_path, "grouped_word_count_*.json"))
    
    # Update nested rules files
    rules_path = "src/data/rules"
    rules_files = glob(os.path.join(rules_path, "nested_*.json"))
    
    all_files = word_count_files + rules_files
    
    for file_path in all_files:
        print(f"Processing {file_path}...")
        update_agency_ids(file_path)
        print(f"Updated {file_path}")

if __name__ == "__main__":
    main() 