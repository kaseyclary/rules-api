import json
from pathlib import Path

def nest_grouped_word_counts(grouped_folder: str, output_folder: str) -> None:
    """
    Process each JSON file in the grouped folder and nest its content within a 
    parent JSON object that includes a "year" field and a "total_word_count" field.
    
    Args:
        grouped_folder (str): Path to the folder containing grouped JSON files.
        output_folder (str): Path to the folder where nested JSON files will be saved.
    """
    grouped_path = Path(grouped_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # Loop through all JSON files in the grouped folder.
    for file in grouped_path.glob("*.json"):
        try:
            # Extract the year from the filename.
            # Expected filename format: "grouped_word_count_2024.json"
            stem = file.stem  # e.g., grouped_word_count_2024
            parts = stem.split("_")
            year = parts[-1] if parts[-1].isdigit() else "unknown"
            
            with file.open('r') as f:
                agencies = json.load(f)
            
            # Sum the total words over all agencies in the file.
            total_word_count = sum(agency.get("total_words", 0) for agency in agencies)

            # Create the nested structure.
            nested_data = {
                "year": year,
                "total_word_count": total_word_count,
                "agencies": agencies
            }
            
            # Write out the new JSON file (same filename) to the output folder.
            output_file = output_path / file.name
            with output_file.open("w") as f:
                json.dump(nested_data, f, indent=4)
            print(f"Processed file {file.name} for year {year}")
        except Exception as e:
            print(f"Error processing {file.name}: {e}")

if __name__ == "__main__":
    input_folder = "src/data/rules/word_counts/grouped"
    output_folder = "src/data/rules/word_counts/nested"
    nest_grouped_word_counts(input_folder, output_folder)