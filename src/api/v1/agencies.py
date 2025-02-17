from fastapi import APIRouter, HTTPException
from typing import List
from src.services.agency_service import AgencyService
from src.services.differences_service import DifferencesService

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_agencies():
    """
    Get all agencies from the database
    """
    try:
        agencies = await AgencyService.get_all_agencies()
        return agencies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-year/{year}", response_model=List[dict])
async def get_agencies_by_year(year: int):
    """
    Get all agencies that have records for a specific year
    
    Args:
        year (int): The year to filter agencies by
    """
    try:
        agencies = await AgencyService.get_agencies_by_year(year)
        return agencies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/year/{agency_year_id}/chapters", response_model=List[dict])
async def get_chapters_by_agency_year(agency_year_id: int):
    """
    Get all chapters for a specific agency year
    
    Args:
        agency_year_id (int): The ID of the agency year to get chapters for
    """
    try:
        chapters = await AgencyService.get_chapters_by_agency_year(agency_year_id)
        return chapters
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chapters/{chapter_id}/rules", response_model=List[dict])
async def get_rules_by_chapter(chapter_id: int):
    """
    Get all rules with their nested subrules for a specific chapter
    
    Args:
        chapter_id (int): The ID of the chapter to get rules for
    """
    try:
        rules = await AgencyService.get_rules_with_subrules_by_chapter(chapter_id)
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/differences", response_model=List[dict])
async def get_differences(start_year: int, end_year: int):
    """
    Get differences in chapters and rules between consecutive years
    
    Args:
        start_year (int): Starting year for comparison
        end_year (int): Ending year for comparison
        
    Returns:
        List of differences between consecutive years
    """
    try:
        differences = await DifferencesService.get_differences_between_years(start_year, end_year)
        return differences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/differences/simple", response_model=List[dict])
async def get_simple_differences(start_year: int, end_year: int):
    """
    Get total differences in chapters and rules between consecutive years
    
    Args:
        start_year (int): Starting year for comparison
        end_year (int): Ending year for comparison
        
    Returns:
        List of total differences between consecutive years
    """
    try:
        differences = await DifferencesService.get_simple_differences_between_years(start_year, end_year)
        return differences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/changes", response_model=dict)
async def get_detailed_changes(year1: int, year2: int):
    """
    Get specific agencies, chapters, and rules that were added or removed between two years
    
    Args:
        year1 (int): First year for comparison
        year2 (int): Second year for comparison
        
    Returns:
        Detailed changes showing added and removed entities at each level
    """
    try:
        changes = await DifferencesService.get_detailed_changes_between_years(year1, year2)
        return changes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rules/totals", response_model=List[dict])
async def get_rules_totals(start_year: int, end_year: int):
    """
    Get total number of rules for each year in the dataset
    
    Args:
        start_year (int): Starting year
        end_year (int): Ending year
        
    Returns:
        List of total rule counts by year
    """
    try:
        totals = await DifferencesService.get_total_rules_by_year(start_year, end_year)
        return totals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rules/new", response_model=List[dict])
async def get_new_rules_count(start_year: int, end_year: int):
    """
    Get count of new rules created each year (rules that didn't exist in previous year)
    
    Args:
        start_year (int): Starting year
        end_year (int): Ending year
        
    Returns:
        List of new rule counts by year
    """
    try:
        counts = await DifferencesService.get_new_rules_count_by_year(start_year, end_year)
        return counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline", response_model=List[dict])
async def get_agency_timeline(start_year: int, end_year: int):
    """
    Get timeline of agency creations and removals between years
    
    Args:
        start_year (int): Starting year
        end_year (int): Ending year
        
    Returns:
        List of agency changes by year
    """
    try:
        timeline = await DifferencesService.get_agency_timeline(start_year, end_year)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/total_rule_volume", response_model=List[dict])
async def get_total_rule_volume(start_year: int, end_year: int):
    """
    Get the total rule volume for each year, which includes the total rule count and 
    the total word count from our word_counts data and our rules data.
    
    Args:
        start_year (int): Starting year.
        end_year (int): Ending year.
    
    Returns:
        List[dict]: A list of dictionaries containing year, total_rules, and total_word_count.
    """
    try:
        volumes = await DifferencesService.get_total_rule_volume_by_year(start_year, end_year)
        return volumes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/agency", response_model=List[dict])
async def get_agency_stats():
    """
    Get aggregated statistics for agencies, including word counts and rule counts
    for both the most recent year and historical data since 2012.
    
    Returns:
        List[dict]: A list of agency statistics
    """
    try:
        stats = await AgencyService.get_agency_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agency/{agency_id}/{year}/details", response_model=dict)
async def get_agency_details_from_local(agency_id: str, year: int):
    """
    Get all chapters and rules for an agency for a given year using local JSON files.
    
    Args:
        agency_id (str): The ID of the agency.
        year (int): The year for which data should be returned.
        
    Returns:
        dict: A dictionary with the agency details (including its chapters and nested rules)
    """
    try:
        result = await AgencyService.get_agency_details_from_local(agency_id, year)
        if not result:
            raise HTTPException(status_code=404, detail="Agency not found for the given year.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
