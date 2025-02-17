from typing import List, Union, Optional
from src.database.config import supabase
import os
import json
from glob import glob
import asyncio

class AgencyService:
    @staticmethod
    async def get_all_agencies() -> List[dict]:
        """
        Retrieve all agencies from the database.
        
        Returns:
            List[dict]: A list of agency records
        """
        response = supabase.table('agencies').select('*').execute()
        return response.data

    @staticmethod
    async def get_agencies_by_year(year: int) -> List[dict]:
        """
        Retrieve all agencies that have records for a specific year.
        
        Args:
            year (int): The year to filter agencies by
            
        Returns:
            List[dict]: A list of agency records that have data for the specified year
        """
        response = supabase.table('agencies')\
            .select('*, agency_years!inner(id, year, total_word_count)')\
            .eq('agency_years.year', year)\
            .execute()
        
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
                    'total_word_count': agency_year['total_word_count']  # Use the agency_year's total_word_count
                }
                unique_agencies[record['id']] = agency_data
        
        return list(unique_agencies.values())

    @staticmethod
    async def get_chapters_by_agency_year(agency_year_id: int) -> List[dict]:
        """
        Retrieve all chapters for a specific agency year.
        
        Args:
            agency_year_id (int): The ID of the agency year
            
        Returns:
            List[dict]: A list of chapter records for the specified agency year
        """
        response = supabase.table('chapters')\
            .select('*')\
            .eq('agency_year_id', agency_year_id)\
            .order('chapter_number')\
            .execute()
        
        return response.data

    @staticmethod
    async def get_rules_with_subrules_by_chapter(chapter_id: int) -> List[dict]:
        """
        Retrieve all rules with their nested subrules for a specific chapter.
        
        Args:
            chapter_id (int): The ID of the chapter
            
        Returns:
            List[dict]: A list of rule records with nested subrules
        """
        response = supabase.table('rules')\
            .select(
                '*,' 
                'subrules:subrules(*)'
            )\
            .eq('chapter_id', chapter_id)\
            .order('citation')\
            .execute()
        
        # Process the response to ensure subrules are properly nested
        rules = []
        for rule in response.data:
            subrules = rule.pop('subrules', [])
            # Sort subrules by subrule_number
            subrules.sort(key=lambda x: x['subrule_number'])
            rule['subrules'] = subrules
            rules.append(rule)
        
        return rules

    @classmethod
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
        base_path = "src/data/rules/word_counts/"
        # Use glob to find all relevant files with the pattern grouped_word_count_*.json.
        file_pattern = os.path.join(base_path, "grouped_word_count_*.json")
        files = glob(file_pattern)
        years = []
        for file in files:
            basename = os.path.basename(file)
            try:
                year_str = basename.replace("grouped_word_count_", "").replace(".json", "")
                year = int(year_str)
                years.append(year)
            except ValueError:
                continue
        if not years:
            raise Exception("No word count files found.")
        recent_year = max(years)
        
        # Load data for the most recent year.
        recent_file = os.path.join(base_path, f"grouped_word_count_{recent_year}.json")
        with open(recent_file, "r") as f:
            recent_data = json.load(f)
        recent_agencies = recent_data.get("agencies", [])
        
        # Build a stats dictionary for each agency appearing in the recent year.
        stats = {}
        for agency in recent_agencies:
            agency_id = agency.get("agency_id")
            agency_name = agency.get("agency")
            # Assume agency-level totals are provided in "total_words" and count rules by counting the chapters.
            recent_total_word_count = agency.get("total_words", 0)
            recent_rules_count = len(agency.get("chapters", []))
            stats[agency_id] = {
                "agency": agency_name,
                "recent_year": recent_year,
                "recent_total_word_count": recent_total_word_count,
                "recent_rules_count": recent_rules_count,
                "yearly_stats": []  # This will hold an array of objects for each year's stats.
            }
        
        # For each year from 2012 up to the most recent year, populate the agency's yearly stats.
        for year in range(2012, recent_year + 1):
            file_path = os.path.join(base_path, f"grouped_word_count_{year}.json")
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
        complexity_score = AgencyService._get_complexity_score(agency_id)

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
            file_path = os.path.join("src", "data", "rules", f"nested_{year}.json")
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r") as f:
                data = json.load(f)
            agencies = data.get("agencies", [])
            for agency in agencies:
                # Use "agencyId" to match the JSON file structure
                if str(agency.get("agencyId")) == str(agency_id):
                    # Add complexity score before returning
                    complexity_score = AgencyService._get_complexity_score(agency_id)
                    agency["complexity_score"] = complexity_score
                    return agency
            return None

        return await asyncio.to_thread(_sync)

    @staticmethod
    def _get_complexity_score(agency_id: Union[str, int]) -> Optional[float]:
        """
        Get the complexity score for an agency from the complexity data file.
        
        Args:
            agency_id (Union[str, int]): The ID of the agency
            
        Returns:
            Optional[float]: The complexity score if found, None otherwise
        """
        try:
            file_path = os.path.join("src", "data", "complexity", "agency_complexity_2024.json")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            for agency in data.get("agencies", []):
                if str(agency.get("agency_id")) == str(agency_id):
                    return agency.get("complexity_index")
            return None
        except Exception:
            return None
