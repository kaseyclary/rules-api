from typing import List, Union, Optional, Dict, Any
from src.database.config import supabase
import os
import json
from glob import glob
import asyncio
from src.services.cache_service import timed_cache
from src.services.file_service import FileService
from datetime import datetime
from pathlib import Path

class AgencyService:
    _db_cache: Dict[str, Any] = {}
    _db_cache_timestamps: Dict[str, datetime] = {}
    _CACHE_DURATION = 3600  # 1 hour in seconds

    @staticmethod
    def _get_cached_db_result(cache_key: str) -> Optional[Any]:
        current_time = datetime.now()
        if (cache_key in AgencyService._db_cache and 
            (current_time - AgencyService._db_cache_timestamps[cache_key]).total_seconds() < AgencyService._CACHE_DURATION):
            return AgencyService._db_cache[cache_key]
        return None

    @staticmethod
    def _set_db_cache(cache_key: str, data: Any) -> None:
        AgencyService._db_cache[cache_key] = data
        AgencyService._db_cache_timestamps[cache_key] = datetime.now()

    @staticmethod
    @timed_cache(expire=3600, cache_name="db_cache")
    async def get_all_agencies() -> List[dict]:
        cache_key = "all_agencies"
        cached_result = AgencyService._get_cached_db_result(cache_key)
        if cached_result is not None:
            return cached_result

        # Offload the synchronous supabase call to a thread.
        response = await asyncio.to_thread(
            lambda: supabase.table('agencies').select('*').execute()
        )
        AgencyService._set_db_cache(cache_key, response.data)
        return response.data

    @staticmethod
    @timed_cache(expire=3600, cache_name="db_cache")
    async def get_agencies_by_year(year: int) -> List[dict]:
        """
        Retrieve all agencies that have records for a specific year.
        
        Args:
            year (int): The year to filter agencies by
            
        Returns:
            List[dict]: A list of agency records that have data for the specified year
        """
        # Offload synchronous supabase call
        response = await asyncio.to_thread(
            lambda: supabase.table('agencies')
                .select('*, agency_years!inner(id, year, total_word_count)')
                .eq('agency_years.year', year)
                .execute()
        )
        
        # Remove duplicate agencies and clean up the response
        unique_agencies = {}
        for record in response.data:
            agency_years = record.pop('agency_years', [])
            if agency_years:
                agency_year = agency_years[0]  # Get the first (and should be only) agency_year
                agency_data = {
                    'id': record['id'],
                    'agency_name': record['agency_name'],
                    'agency_number': record['agency_number'],
                    'created_date': record['created_date'],
                    'last_modified_date': record['last_modified_date'],
                    'agency_year_id': agency_year['id'],
                    'total_word_count': agency_year['total_word_count']
                }
                unique_agencies[record['id']] = agency_data
        
        return list(unique_agencies.values())

    @staticmethod
    @timed_cache(expire=3600, cache_name="db_cache")
    async def get_chapters_by_agency_year(agency_year_id: int) -> List[dict]:
        """
        Retrieve all chapters for a specific agency year.
        
        Args:
            agency_year_id (int): The ID of the agency year
            
        Returns:
            List[dict]: A list of chapter records for the specified agency year
        """
        # Offload the supabase call to a thread.
        response = await asyncio.to_thread(
            lambda: supabase.table('chapters')
                .select('*')
                .eq('agency_year_id', agency_year_id)
                .order('chapter_number')
                .execute()
        )
        return response.data

    @staticmethod
    @timed_cache(expire=3600, cache_name="db_cache")
    async def get_rules_with_subrules_by_chapter(chapter_id: int) -> List[dict]:
        """
        Retrieve all rules with their nested subrules for a specific chapter.
        
        Args:
            chapter_id (int): The ID of the chapter
            
        Returns:
            List[dict]: A list of rule records with nested subrules
        """
        # Offload the supabase call.
        response = await asyncio.to_thread(
            lambda: supabase.table('rules')
                .select('*, subrules:subrules(*)')
                .eq('chapter_id', chapter_id)
                .order('citation')
                .execute()
        )
        
        # Process the response to ensure subrules are properly nested
        rules = []
        for rule in response.data:
            subrules = rule.pop('subrules', [])
            subrules.sort(key=lambda x: x['subrule_number'])
            rule['subrules'] = subrules
            rules.append(rule)
        
        return rules

    @classmethod
    @timed_cache(expire=3600, cache_name="db_cache")
    async def get_agency_stats(cls):
        """
        Aggregates rules and word count statistics for agencies that appear in the most recent year.
        For each agency, it finds:
          - the totals for the most recent year (from its grouped word count file)
          - the totals for rules and word count, accumulating data from 2012 through the recent year.
        """
        return await asyncio.to_thread(cls._get_agency_stats_sync)

    @classmethod
    def _get_agency_stats_sync(cls):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        base_path = BASE_DIR / "src" / "data" / "rules" / "word_counts"
        years = FileService.get_available_years(str(base_path), "grouped_word_count")
        if not years:
            raise Exception("No word count files found.")
        recent_year = max(years)
        
        # Load nested data
        nested_file = BASE_DIR / "src" / "data" / "rules" / f"nested_{recent_year}.json"
        nested_data = FileService.read_json_file(nested_file)
        nested_agencies_lookup = {}
        if nested_data.get("agencies", []):
            for agency in nested_data.get("agencies", []):
                agency_id = agency.get("agencyId")
                if agency_id is not None:
                    total_rule_count = 0
                    for chapter in agency.get("chapters", []):
                        total_rule_count += chapter.get("ruleCount", len(chapter.get("rules", [])))
                    nested_agencies_lookup[str(agency_id)] = total_rule_count
        
        # Load data for the most recent year
        recent_file = base_path / f"grouped_word_count_{recent_year}.json"
        with open(recent_file, "r") as f:
            recent_data = json.load(f)
        recent_agencies = recent_data.get("agencies", [])
        
        stats = {}
        for agency in recent_agencies:
            agency_id = agency.get("agency_id")
            agency_name = agency.get("agency")
            recent_total_word_count = agency.get("total_words", 0)
            
            # Get rule count from nested data if available, otherwise fall back to chapter count
            recent_rules_count = nested_agencies_lookup.get(str(agency_id))
            if recent_rules_count is None:
                recent_rules_count = len(agency.get("chapters", []))
            
            complexity_score = cls._get_complexity_score(agency_id, agency_name)
            stats[agency_id] = {
                "agency_id": agency_id,
                "agency": agency_name,
                "recent_year": recent_year,
                "recent_total_word_count": recent_total_word_count,
                "recent_rules_count": recent_rules_count,
                "complexity_score": complexity_score,
                "yearly_stats": []
            }
        
        # For each year from 2012 up to the most recent year, populate the agency's yearly stats.
        for year in range(2012, recent_year + 1):
            file_path = base_path / f"grouped_word_count_{year}.json"
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                for agency in data.get("agencies", []):
                    agency_id = agency.get("agency_id")
                    # Only add if the agency appears in the recent year.
                    if agency_id in stats:
                        stats[agency_id]["yearly_stats"].append({
                            "year": year,
                            "total_word_count": agency.get("total_words", 0),
                            "rules_count": len(agency.get("chapters", []))
                        })
        
        return list(stats.values())

    @staticmethod
    @timed_cache(expire=3600, cache_name="db_cache")
    async def get_agency_data_for_year(agency_id: int, year: int) -> dict:
        """
        Retrieve all chapters and associated rules for a specific agency in a given year.
        
        Args:
            agency_id (int): The ID of the agency.
            year (int): The year to retrieve data for.
            
        Returns:
            dict: A dictionary containing agency details and a list of chapters with their rules.
                  Example:
                  {
                      "agency": {
                          "id": 1,
                          "agency_name": "Department of Education",
                          "agency_number": "123"
                      },
                      "year": 2022,
                      "chapters": [
                          {
                              "id": 10,
                              "chapter": "CHAPTER TITLE",
                              ...
                              "rules": [ {...}, {...} ]
                          },
                          ...
                      ]
                  }
        """
        # Query the agency record with nested agency_years for the specified year.
        response = supabase.table("agencies") \
                    .select("*, agency_years!inner(id, year)") \
                    .eq("id", agency_id) \
                    .eq("agency_years.year", year) \
                    .execute()
        agencies = response.data
        if not agencies:
            return None

        agency_record = agencies[0]
        agency_years = agency_record.get("agency_years", [])
        if not agency_years:
            return None

        agency_year_id = agency_years[0].get("id")
        # Retrieve chapters for the agency year.
        chapters = await AgencyService.get_chapters_by_agency_year(agency_year_id)

        # For each chapter, retrieve its rules concurrently.
        rules_tasks = [AgencyService.get_rules_with_subrules_by_chapter(chapter["id"]) for chapter in chapters]
        chapters_rules = await asyncio.gather(*rules_tasks)

        # Attach the rules to their corresponding chapter.
        for chapter, rules in zip(chapters, chapters_rules):
            chapter["rules"] = rules

        # Get complexity score before return
        complexity_score = AgencyService._get_complexity_score(agency_id, agency_record.get("agency_name"))

        # Return the combined result.
        return {
            "agency": {
                "id": agency_record.get("id"),
                "agency_name": agency_record.get("agency_name"),
                "agency_number": agency_record.get("agency_number"),
                "complexity_score": complexity_score
            },
            "year": year,
            "chapters": chapters
        }

    @staticmethod
    async def get_agency_details_from_local(agency_id: Union[str, int], year: int) -> Optional[dict]:
        """
        Retrieve all chapters and rules for an agency for a given year using local JSON files.
        
        Args:
            agency_id (str or int): The ID of the agency.
            year (int): The year for which to retrieve the data.
            
        Returns:
            dict: A dictionary containing the agency details (including chapters with their nested rules)
                  or None if the agency or file is not found.
        """
        def _sync():
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            file_path = BASE_DIR / "src" / "data" / "rules" / f"nested_{year}.json"
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r") as f:
                data = json.load(f)
            agencies = data.get("agencies", [])
            for agency in agencies:
                # Use "agencyId" to match the JSON file structure
                if str(agency.get("agencyId")) == str(agency_id):
                    # Add complexity score before returning
                    complexity_score = AgencyService._get_complexity_score(
                        agency_id, 
                        agency.get("agencyName")
                    )
                    agency["complexity_score"] = complexity_score
                    return agency
            return None

        return await asyncio.to_thread(_sync)

    @staticmethod
    def _get_complexity_score(agency_id: Union[str, int], agency_name: str = None) -> Optional[float]:
        """
        Get the complexity score for an agency from the complexity data file.
        
        Args:
            agency_id (Union[str, int]): The ID of the agency
            agency_name (str, optional): The name of the agency, used as fallback for specific cases
            
        Returns:
            Optional[float]: The complexity score if found, None otherwise
        """
        try:
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            file_path = BASE_DIR / "src" / "data" / "complexity" / "agency_complexity_2024.json"
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # First try to match by ID
            for agency in data.get("agencies", []):
                if str(agency.get("agency_id")) == str(agency_id):
                    return agency.get("complexity_index")
            
            # If ID match fails and we have a name, try name matching for specific cases
            if agency_name and "Engineering and Land Surveying Examining Board" in agency_name:
                for agency in data.get("agencies", []):
                    if "Engineering and Land Surveying Examining Board" in agency.get("agency", ""):
                        return agency.get("complexity_index")
                    
            return None
        except Exception:
            return None
