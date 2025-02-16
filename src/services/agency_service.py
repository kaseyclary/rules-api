from typing import List
from src.database.config import supabase

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
