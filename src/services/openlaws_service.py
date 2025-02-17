import os
import requests
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

OPENLAWS_API_KEY = os.getenv("OPENLAWS_API_KEY")
OPENLAWS_BASE_URL = os.getenv("OPENLAWS_BASE_URL")

def convert_to_bluebook_citation(chapter_rule: str) -> str:
    """
    Convert our internal chapter/rule format (e.g., "441.1.1")
    into the citation format expected by OpenLaws for a citation lookup.
    
    For Iowa Admin. Code r. citations, the citation should be in the format:
      Iowa Admin. Code r. {chapter}-{section}.{rule}
      
    For example, "441.1.1" becomes "Iowa Admin. Code r. 441-1.1".
    """
    parts = chapter_rule.split(".")
    if len(parts) != 3:
        raise ValueError("Input must be in the format 'chapter.rule.rulePart'")
    chapter, section, rule = parts
    citation = f"Iowa Admin. Code r. {chapter}-{section}.{rule}"
    return citation

def get_iowa_rule(chapter_rule: str) -> dict:
    """
    Query the OpenLaws API using the citations endpoint for a law division based on a chapter/rule string.
    
    The provided chapter_rule (e.g., "441.1.1") is used to derive the citation.
    We use the Iowa jurisdiction ("IA") for this query.
    
    Returns:
      A dictionary with the API's JSON response.
    """
    # Convert our internal format to the citation.
    citation = convert_to_bluebook_citation(chapter_rule)
    
    # Use hard-coded value for the Iowa jurisdiction.
    jurisdiction_id = "IA"
    
    # Construct the endpoint URL.
    endpoint = f"{OPENLAWS_BASE_URL}/api/v1/jurisdictions/{jurisdiction_id}/laws/citations"
    
    # Set up query parameters with the citation.
    params = {"query": citation}
    
    headers = {
        "Authorization": f"Bearer {OPENLAWS_API_KEY}"
    }
    
    # Print the full request URL and parameters for troubleshooting.
    print(f"Requesting URL: {endpoint} with params: {params}")
    
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()  # Raise an error for non-200 responses.
    return response.json()

if __name__ == "__main__":
    # Example usage
    test_input = "441.1.1"
    try:
        data = get_iowa_rule(test_input)
        print("API Response:", data)
    except Exception as e:
        print("Error:", e)