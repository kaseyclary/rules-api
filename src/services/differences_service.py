import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from src.services.cache_service import timed_cache
from functools import lru_cache
from datetime import datetime

class DifferencesService:
    _differences_cache: Dict[Tuple[int, int], List[dict]] = {}
    _differences_timestamps: Dict[Tuple[int, int], datetime] = {}
    _CACHE_DURATION = 3600

    @staticmethod
    def _get_cached_differences(start_year: int, end_year: int) -> Optional[List[dict]]:
        key = (start_year, end_year)
        current_time = datetime.now()
        if (key in DifferencesService._differences_cache and 
            (current_time - DifferencesService._differences_timestamps[key]).total_seconds() < DifferencesService._CACHE_DURATION):
            return DifferencesService._differences_cache[key]
        return None

    @staticmethod
    def _set_differences_cache(start_year: int, end_year: int, data: List[dict]) -> None:
        key = (start_year, end_year)
        DifferencesService._differences_cache[key] = data
        DifferencesService._differences_timestamps[key] = datetime.now()

    @staticmethod
    @timed_cache(expire=3600, cache_name="differences_cache")
    async def get_differences_between_years(start_year: int, end_year: int) -> List[dict]:
        """
        Calculate differences between consecutive years for agencies, chapters, and rules.
        Positive numbers indicate additions, negative numbers indicate reductions.
        
        Args:
            end_year (int): Ending year for comparison
            
        Returns:
            List[dict]: A list of year-over-year differences
        """
        cached_result = DifferencesService._get_cached_differences(start_year, end_year)
        if cached_result:
            return cached_result

        differences = []
        data_dir = Path("src/data/rules")
        
        for year in range(start_year + 1, end_year + 1):
            current_year = year
            previous_year = year - 1
            
            # Load data from JSON files
            current_file = data_dir / f"nested_{current_year}.json"
            previous_file = data_dir / f"nested_{previous_year}.json"
            
            try:
                with open(current_file, 'r') as f:
                    current_data = json.load(f)
                with open(previous_file, 'r') as f:
                    previous_data = json.load(f)
                    
                # Calculate agency-level differences
                agency_differences = DifferencesService._calculate_agency_differences(
                    json.dumps(previous_data['agencies']),
                    json.dumps(current_data['agencies'])
                )
                
                # Calculate total differences across all agencies
                total_chapters_diff = sum(diff['chapter_difference'] for diff in agency_differences)
                total_rules_diff = sum(diff['rule_difference'] for diff in agency_differences)
                
                year_diff = {
                    'year': current_year,
                    'previous_year': previous_year,
                    'total_differences': {
                        'chapters': total_chapters_diff,
                        'rules': total_rules_diff
                    },
                    'agency_differences': agency_differences
                }
                
                differences.append(year_diff)
                
            except FileNotFoundError as e:
                print(f"Warning: Could not find data file for year {year} or {previous_year}")
                continue
                
        DifferencesService._set_differences_cache(start_year, end_year, differences)
        return differences

    @staticmethod
    @lru_cache(maxsize=128)
    def _calculate_agency_differences(prev_agencies_str: str, curr_agencies_str: str) -> List[dict]:
        """
        Memoized version of difference calculation
        """
        prev_agencies = json.loads(prev_agencies_str)
        curr_agencies = json.loads(curr_agencies_str)
        differences = []
        
        # Create lookup dictionaries
        prev_lookup = {agency['agencyId']: agency for agency in prev_agencies}
        curr_lookup = {agency['agencyId']: agency for agency in curr_agencies}
        
        # Get all unique agency IDs
        all_agency_ids = set(prev_lookup.keys()) | set(curr_lookup.keys())
        
        for agency_id in all_agency_ids:
            prev_agency = prev_lookup.get(agency_id, {'chapterCount': 0, 'chapters': []})
            curr_agency = curr_lookup.get(agency_id, {'chapterCount': 0, 'chapters': []})
            
            # Calculate rule counts
            prev_rule_count = sum(chapter.get('ruleCount', 0) for chapter in prev_agency.get('chapters', []))
            curr_rule_count = sum(chapter.get('ruleCount', 0) for chapter in curr_agency.get('chapters', []))
            
            # Calculate differences (newer minus older)
            chapter_diff = curr_agency['chapterCount'] - prev_agency['chapterCount']
            rule_diff = curr_rule_count - prev_rule_count
            
            # Only include agencies that had changes
            if chapter_diff != 0 or rule_diff != 0:
                diff = {
                    'agency_id': agency_id,
                    'agency_name': curr_agency.get('agencyName', prev_agency.get('agencyName', 'Unknown')),
                    'chapter_difference': chapter_diff,
                    'rule_difference': rule_diff
                }
                differences.append(diff)
            
        return differences

    @staticmethod
    def _calculate_total_chapters_difference(previous_agencies: List[dict], current_agencies: List[dict]) -> int:
        """Calculate total chapter count difference"""
        prev_total = sum(agency['chapterCount'] for agency in previous_agencies)
        curr_total = sum(agency['chapterCount'] for agency in current_agencies)
        return curr_total - prev_total

    @staticmethod
    def _calculate_total_rules_difference(previous_agencies: List[dict], current_agencies: List[dict]) -> int:
        """Calculate total rule count difference"""
        prev_total = sum(
            chapter.get('ruleCount', 0)
            for agency in previous_agencies
            for chapter in agency.get('chapters', [])
        )
        curr_total = sum(
            chapter.get('ruleCount', 0)
            for agency in current_agencies
            for chapter in agency.get('chapters', [])
        )
        return curr_total - prev_total

    @staticmethod
    @timed_cache(expire=3600)
    async def get_simple_differences_between_years(start_year: int, end_year: int) -> List[dict]:
        """
        Calculate total differences between consecutive years for chapters and rules,
        and include total laws for each year.
        
        Args:
            start_year (int): Starting year for comparison
            end_year (int): Ending year for comparison
            
        Returns:
            List[dict]: A list of year-over-year total differences and law counts
        """
        differences = []
        data_dir = Path("src/data/rules")
        
        for year in range(start_year + 1, end_year + 1):
            current_year = year
            previous_year = year - 1
            
            # Load data from JSON files
            current_file = data_dir / f"nested_{current_year}.json"
            previous_file = data_dir / f"nested_{previous_year}.json"
            
            try:
                with open(current_file, 'r') as f:
                    current_data = json.load(f)
                with open(previous_file, 'r') as f:
                    previous_data = json.load(f)
                    
                # Use the same calculation methods as the detailed endpoint
                total_chapters_diff = DifferencesService._calculate_total_chapters_difference(
                    previous_data['agencies'],
                    current_data['agencies']
                )
                total_rules_diff = DifferencesService._calculate_total_rules_difference(
                    previous_data['agencies'],
                    current_data['agencies']
                )
                
                # Get total laws for current year
                total_laws = DifferencesService._get_law_count_for_year(current_year)
                
                year_diff = {
                    'year': current_year,
                    'previous_year': previous_year,
                    'chapter_difference': total_chapters_diff,
                    'rule_difference': total_rules_diff,
                    'total_laws': total_laws
                }
                
                differences.append(year_diff)
                
            except FileNotFoundError as e:
                print(f"Warning: Could not find data file for year {year} or {previous_year}")
                continue
                
        return differences

    @staticmethod
    @timed_cache(expire=3600)
    async def get_detailed_changes_between_years(year1: int, year2: int) -> dict:
        """
        Get specific agencies, chapters and rules that were added or removed between two years.
        
        Args:
            year1 (int): First year for comparison
            year2 (int): Second year for comparison
            
        Returns:
            dict: Detailed changes showing added and removed entities
        """
        data_dir = Path("src/data/rules")
        
        # Load data from JSON files
        year1_file = data_dir / f"nested_{year1}.json"
        year2_file = data_dir / f"nested_{year2}.json"
        
        try:
            with open(year1_file, 'r') as f:
                year1_data = json.load(f)
            with open(year2_file, 'r') as f:
                year2_data = json.load(f)
                
            changes = {
                'year1': year1,
                'year2': year2,
                'agencies': {
                    'added': [],
                    'removed': []
                },
                'chapters': {
                    'added': [],
                    'removed': []
                },
                'rules': {
                    'added': [],
                    'removed': []
                }
            }
            
            # Create lookup dictionaries for agencies
            year1_agencies = {agency['agencyId']: agency for agency in year1_data['agencies']}
            year2_agencies = {agency['agencyId']: agency for agency in year2_data['agencies']}
            
            # Find added and removed agencies
            for agency_id in set(year2_agencies.keys()) - set(year1_agencies.keys()):
                agency = year2_agencies[agency_id]
                changes['agencies']['added'].append({
                    'agency_id': agency['agencyId'],
                    'agency_name': agency['agencyName']
                })
                
            for agency_id in set(year1_agencies.keys()) - set(year2_agencies.keys()):
                agency = year1_agencies[agency_id]
                changes['agencies']['removed'].append({
                    'agency_id': agency['agencyId'],
                    'agency_name': agency['agencyName']
                })
            
            # Track chapters and rules across all agencies
            year1_chapters = {}
            year2_chapters = {}
            year1_rules = {}
            year2_rules = {}
            
            # Build chapter and rule lookups for year1
            for agency in year1_data['agencies']:
                for chapter in agency.get('chapters', []):
                    chapter_key = f"{agency['agencyId']}_{chapter['chapterId']}"
                    year1_chapters[chapter_key] = {
                        'agency_id': agency['agencyId'],
                        'agency_name': agency['agencyName'],
                        'chapter_id': chapter['chapterId'],
                        'chapter_title': chapter['chapterTitle']
                    }
                    
                    for rule in chapter.get('rules', []):
                        rule_key = f"{chapter_key}_{rule['ruleNumber']}"
                        year1_rules[rule_key] = {
                            'agency_id': agency['agencyId'],
                            'agency_name': agency['agencyName'],
                            'chapter_id': chapter['chapterId'],
                            'chapter_title': chapter['chapterTitle'],
                            'rule_number': rule['ruleNumber'],
                            'rule_title': rule['ruleTitle']
                        }
            
            # Build chapter and rule lookups for year2
            for agency in year2_data['agencies']:
                for chapter in agency.get('chapters', []):
                    chapter_key = f"{agency['agencyId']}_{chapter['chapterId']}"
                    year2_chapters[chapter_key] = {
                        'agency_id': agency['agencyId'],
                        'agency_name': agency['agencyName'],
                        'chapter_id': chapter['chapterId'],
                        'chapter_title': chapter['chapterTitle']
                    }
                    
                    for rule in chapter.get('rules', []):
                        rule_key = f"{chapter_key}_{rule['ruleNumber']}"
                        year2_rules[rule_key] = {
                            'agency_id': agency['agencyId'],
                            'agency_name': agency['agencyName'],
                            'chapter_id': chapter['chapterId'],
                            'chapter_title': chapter['chapterTitle'],
                            'rule_number': rule['ruleNumber'],
                            'rule_title': rule['ruleTitle']
                        }
            
            # Find added and removed chapters
            for chapter_key in set(year2_chapters.keys()) - set(year1_chapters.keys()):
                changes['chapters']['added'].append(year2_chapters[chapter_key])
            
            for chapter_key in set(year1_chapters.keys()) - set(year2_chapters.keys()):
                changes['chapters']['removed'].append(year1_chapters[chapter_key])
            
            # Find added and removed rules
            for rule_key in set(year2_rules.keys()) - set(year1_rules.keys()):
                changes['rules']['added'].append(year2_rules[rule_key])
            
            for rule_key in set(year1_rules.keys()) - set(year2_rules.keys()):
                changes['rules']['removed'].append(year1_rules[rule_key])
            
            return changes
            
        except FileNotFoundError as e:
            print(f"Warning: Could not find data file for year {year1} or {year2}")
            raise e 

    @staticmethod
    def _get_law_count_for_year(year: int) -> int:
        """
        Get the total number of laws (signed bills) for a specific year.
        
        Args:
            year (int): The year to get law count for
            
        Returns:
            int: Total number of laws for the year
        """
        try:
            with open(f"src/data/laws/signed_bills_{year}.json", 'r') as f:
                data = json.load(f)
                return data.get('totalBills', 0)
        except FileNotFoundError:
            print(f"Warning: Could not find signed bills file for year {year}")
            return 0 

    @staticmethod
    async def get_total_rules_by_year(start_year: int, end_year: int) -> List[dict]:
        """
        Get the total number of rules for each year in the dataset.
        
        Args:
            start_year (int): Starting year
            end_year (int): Ending year
            
        Returns:
            List[dict]: A list of total rule counts by year
        """
        totals = []
        data_dir = Path("src/data/rules")
        
        for year in range(start_year, end_year + 1):
            file_path = data_dir / f"nested_{year}.json"
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                total_rules = sum(
                    chapter.get('ruleCount', 0)
                    for agency in data['agencies']
                    for chapter in agency.get('chapters', [])
                )
                
                year_total = {
                    'year': year,
                    'total_rules': total_rules
                }
                
                totals.append(year_total)
                    
            except FileNotFoundError as e:
                print(f"Warning: Could not find data file for year {year}")
                continue
                
        return totals 

    @staticmethod
    async def get_new_rules_count_by_year(start_year: int, end_year: int) -> List[dict]:
        """
        Get the count of new rules and total laws for each year.
        
        Args:
            start_year (int): Starting year
            end_year (int): Ending year
            
        Returns:
            List[dict]: A list of new rule counts and total laws by year
        """
        new_rule_counts = []
        data_dir = Path("src/data/rules")
        
        for year in range(start_year + 1, end_year + 1):
            current_year = year
            previous_year = year - 1
            
            try:
                # Load current and previous year data
                with open(data_dir / f"nested_{current_year}.json", 'r') as f:
                    current_data = json.load(f)
                with open(data_dir / f"nested_{previous_year}.json", 'r') as f:
                    previous_data = json.load(f)
                
                # Get all rule numbers from both years
                current_rules = set()
                previous_rules = set()
                
                # Collect rule numbers from current year
                for agency in current_data['agencies']:
                    for chapter in agency.get('chapters', []):
                        for rule in chapter.get('rules', []):
                            current_rules.add(rule['ruleNumber'])
                
                # Collect rule numbers from previous year
                for agency in previous_data['agencies']:
                    for chapter in agency.get('chapters', []):
                        for rule in chapter.get('rules', []):
                            previous_rules.add(rule['ruleNumber'])
                
                # Calculate new rules (rules in current year that weren't in previous year)
                new_rules_count = len(current_rules - previous_rules)
                
                # Get total laws for current year using existing method
                total_laws = DifferencesService._get_law_count_for_year(current_year)
                
                year_count = {
                    'year': current_year,
                    'new_rules_count': new_rules_count,
                    'total_laws': total_laws
                }
                
                new_rule_counts.append(year_count)
                
            except FileNotFoundError as e:
                print(f"Warning: Could not find data file for year {year} or {previous_year}")
                continue
                
        return new_rule_counts 

    @staticmethod
    async def get_agency_timeline(start_year: int, end_year: int) -> List[dict]:
        """
        Create a timeline of agency creations and removals between consecutive years.
        
        Args:
            start_year (int): Starting year for analysis
            end_year (int): Ending year for analysis
            
        Returns:
            List[dict]: Timeline of agency changes by year
        """
        timeline = []
        data_dir = Path("src/data/rules")
        
        for year in range(start_year + 1, end_year + 1):
            current_year = year
            previous_year = year - 1
            
            try:
                # Load data from consecutive years
                with open(data_dir / f"nested_{current_year}.json", 'r') as f:
                    current_data = json.load(f)
                with open(data_dir / f"nested_{previous_year}.json", 'r') as f:
                    previous_data = json.load(f)
                
                # Create lookup dictionaries for agencies
                current_agencies = {agency['agencyId']: agency for agency in current_data['agencies']}
                previous_agencies = {agency['agencyId']: agency for agency in previous_data['agencies']}
                
                # Find new and removed agencies
                new_agencies = []
                removed_agencies = []
                
                for agency_id in set(current_agencies.keys()) - set(previous_agencies.keys()):
                    agency = current_agencies[agency_id]
                    new_agencies.append({
                        'agency_id': agency['agencyId'],
                        'agency_name': agency['agencyName']
                    })
                
                for agency_id in set(previous_agencies.keys()) - set(current_agencies.keys()):
                    agency = previous_agencies[agency_id]
                    removed_agencies.append({
                        'agency_id': agency['agencyId'],
                        'agency_name': agency['agencyName']
                    })
                
                # Only add years with changes to the timeline
                if new_agencies or removed_agencies:
                    year_changes = {
                        'year': current_year,
                        'created': new_agencies,
                        'removed': removed_agencies
                    }
                    timeline.append(year_changes)
                    
            except FileNotFoundError:
                print(f"Warning: Could not find data file for year {current_year} or {previous_year}")
                continue
        
        return timeline

    @staticmethod
    async def get_total_rule_volume_by_year(start_year: int, end_year: int) -> List[dict]:
        """
        Calculate the total rule volume for each year which includes the total rule count
        from our rules data and the total word count from our word_counts data.
        
        Args:
            start_year (int): Starting year.
            end_year (int): Ending year.
        
        Returns:
            List[dict]: A list of dictionaries containing year, total_rules, and total_word_count.
        """
        volumes = []
        rules_dir = Path("src/data/rules")
        word_counts_dir = Path("src/data/rules/word_counts")
        
        for year in range(start_year, end_year + 1):
            # Get total rule count from the rules file.
            rules_file = rules_dir / f"nested_{year}.json"
            try:
                with open(rules_file, "r") as f:
                    data = json.load(f)
            except FileNotFoundError:
                print(f"Warning: Could not find rules file for year {year}")
                continue
            
            total_rules = sum(
                len(chapter.get("rules", []))
                for agency in data.get("agencies", [])
                for chapter in agency.get("chapters", [])
            )
            
            # Get total word count from the word_counts file.
            word_count_file = word_counts_dir / f"grouped_word_count_{year}.json"
            try:
                with open(word_count_file, "r") as f:
                    wc_data = json.load(f)
                total_word_count = wc_data.get("total_word_count", 0)
            except FileNotFoundError:
                print(f"Warning: Could not find word count file for year {year}")
                total_word_count = 0
            
            volumes.append({
                "year": year,
                "total_rules": total_rules,
                "total_word_count": total_word_count
            })
        
        return volumes

def scrape_agency_timeline(start_year: int, end_year: int) -> List[dict]:
    """
    Create a timeline of agency creations and removals between years.
    
    Args:
        start_year (int): Starting year for analysis
        end_year (int): Ending year for analysis
        
    Returns:
        List[dict]: Timeline of agency changes by year
    """
    timeline = []
    data_dir = Path("src/data/rules")
    
    for year in range(start_year + 1, end_year + 1):
        current_year = year
        previous_year = year - 1
        
        try:
            # Load data from consecutive years
            with open(data_dir / f"nested_{current_year}.json", 'r') as f:
                current_data = json.load(f)
            with open(data_dir / f"nested_{previous_year}.json", 'r') as f:
                previous_data = json.load(f)
            
            # Create lookup dictionaries for agencies
            current_agencies = {agency['agencyId']: agency for agency in current_data['agencies']}
            previous_agencies = {agency['agencyId']: agency for agency in previous_data['agencies']}
            
            # Find new and removed agencies
            new_agencies = []
            removed_agencies = []
            
            for agency_id in set(current_agencies.keys()) - set(previous_agencies.keys()):
                agency = current_agencies[agency_id]
                new_agencies.append({
                    'agency_id': agency['agencyId'],
                    'agency_name': agency['agencyName']
                })
            
            for agency_id in set(previous_agencies.keys()) - set(current_agencies.keys()):
                agency = previous_agencies[agency_id]
                removed_agencies.append({
                    'agency_id': agency['agencyId'],
                    'agency_name': agency['agencyName']
                })
            
            # Only add years with changes to the timeline
            if new_agencies or removed_agencies:
                year_changes = {
                    'year': current_year,
                    'created': new_agencies,
                    'removed': removed_agencies
                }
                timeline.append(year_changes)
                
        except FileNotFoundError:
            print(f"Warning: Could not find data file for year {current_year} or {previous_year}")
            continue
    
    return timeline

if __name__ == "__main__":
    # Example usage
    timeline = scrape_agency_timeline(1998, 2025)
    
    # Print the timeline in a readable format
    for entry in timeline:
        print(f"\nYear: {entry['year']}")
        
        if entry['created']:
            print("\nCreated Agencies:")
            for agency in entry['created']:
                print(f"- {agency['agency_name']} (ID: {agency['agency_id']})")
                
        if entry['removed']:
            print("\nRemoved Agencies:")
            for agency in entry['removed']:
                print(f"- {agency['agency_name']} (ID: {agency['agency_id']})") 