import json
import math
import os

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def main():
    # Define input file paths
    grouped_path = "src/data/rules/word_counts/grouped_word_count_2024.json"
    nested_path  = "src/data/rules/nested_2024.json"
    
    # Define the output directory and file path
    output_dir = "data/complexity"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "agency_complexity_2024.json")
    
    # Load JSON data from both input files
    grouped_data = load_json(grouped_path)
    nested_data  = load_json(nested_path)
    
    # Determine the list of agencies from the grouped data.
    if isinstance(grouped_data, list):
        agencies_list = grouped_data
    elif isinstance(grouped_data, dict):
        if "agencies" in grouped_data:
            agencies_list = grouped_data["agencies"]
        else:
            agencies_list = [grouped_data]
    else:
        print("Unexpected format in grouped data.")
        return
    
    # Build a lookup from the nested file keyed by agencyId.
    # For each nested agency, sum the ruleCount from each chapter.
    nested_agencies_lookup = {}
    for agency in nested_data.get("agencies", []):
        agency_id = agency.get("agencyId")
        if agency_id is not None:
            total_rule_count = 0
            for chapter in agency.get("chapters", []):
                # Use "ruleCount" if available; otherwise, count the length of the "rules" array.
                total_rule_count += chapter.get("ruleCount", len(chapter.get("rules", [])))
            nested_agencies_lookup[str(agency_id)] = total_rule_count

    results = []
    avg_values = []
    
    # Process every agency found in the grouped file.
    for agency in agencies_list:
        agency_id = agency.get("agency_id")
        agency_name = agency.get("agency")
        total_words = agency.get("total_words", 0)
        
        # Look for the rule count using the nested lookup (using agency_id/agencyId),
        # or fall back to counting chapters if not found.
        rule_count = None
        if agency_id is not None:
            rule_count = nested_agencies_lookup.get(str(agency_id))
        if rule_count is None:
            rule_count = len(agency.get("chapters", []))
        
        # Avoid division by zero
        if rule_count == 0:
            continue

        avg_words = total_words / rule_count
        avg_values.append(avg_words)
        
        results.append({
            "agency": agency_name,
            "agency_id": agency_id,
            "total_words": total_words,
            "rule_count": rule_count,
            "avg_words_per_rule": avg_words
        })
    
    if not results:
        print("No agency data found for processing.")
        return
    
    # Use linear scaling instead of logarithmic
    min_avg = min(avg_values)
    max_avg = max(avg_values)
    
    if min_avg == max_avg:
        for item in results:
            item["complexity_index"] = 60
    else:
        # Take log of all values
        log_values = [math.log(x) for x in avg_values]
        min_log = min(log_values)
        max_log = max(log_values)
        
        for item in results:
            current_avg = item["avg_words_per_rule"]
            # Log transform the current value
            log_current = math.log(current_avg)
            # Normalize using log values to 20-100 range
            normalized = (log_current - min_log) / (max_log - min_log)
            complexity = 20 + normalized * 80  # 80 = (100 - 20)
            item["complexity_index"] = round(complexity, 2)
    
    output_data = {
        "year": "2024",
        "agencies": results
    }
    
    save_json(output_data, output_path)
    print(f"Agency complexity index calculated for {len(results)} agencies and saved to {output_path}.")

if __name__ == "__main__":
    main()