from pathlib import Path
import json

def count_total_chapters():
    """Count total number of chapters across all years 1998-2025"""
    data_dir = Path("src/data/rules")
    total_chapters = 0
    
    for year in range(1998, 2026):
        file_path = data_dir / f"nested_{year}.json"
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                year_total = sum(agency['chapterCount'] for agency in data['agencies'])
                total_chapters += year_total
                
        except FileNotFoundError:
            print(f"Warning: Could not find data file for year {year}")
            continue
    
    print(f"Total chapters across all years (1998-2025): {total_chapters}")

if __name__ == "__main__":
    count_total_chapters() 