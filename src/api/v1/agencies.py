from fastapi import APIRouter, HTTPException
from typing import List
from src.services.agency_service import AgencyService

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
