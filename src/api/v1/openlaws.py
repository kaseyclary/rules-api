from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from src.services.openlaws_service import get_iowa_rule

router = APIRouter()

@router.get("/rule/{chapter_rule}", response_model=dict, summary="Get Iowa Rule")
async def get_iowa_rule_endpoint(chapter_rule: str):
    """
    Retrieve an Iowa rule using the OpenLaws service.

    Args:
        chapter_rule (str): The chapter.rule string (e.g. "441.1.1")

    Returns:
        dict: Law division data from the OpenLaws API.
    """
    try:
        # Since get_iowa_rule() makes a blocking HTTP call, run it in a threadpool.
        result = await run_in_threadpool(get_iowa_rule, chapter_rule)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 