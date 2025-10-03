import os

from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Questions to ask the LLM about each paper that appear in the research output table
LLM_QUESTIONS = [
    "What is the main physics phenomenon studied by this paper",
    "Is this work related to dark matter searches? If yes, how?",
    "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?",
]

# Additional question for ML4DM detection (used only for Mattermost notifications, not in output table)
ML4DM_DETECTION_QUESTION = "Does this paper use ML techniques for dark matter searches? And if yes, list the main ML techniques used in this paper"

def get_llm_questions():
    """
    Get the LLM questions for the research output table (same for local and CI).
    
    Returns:
        list: LLM questions for the main research table
    """
    return LLM_QUESTIONS

def get_ci_analysis_questions():
    """
    Get all questions for CI analysis (table questions + ML4DM detection).
    
    Returns:
        list: All questions needed for CI analysis including ML4DM detection
    """
    return LLM_QUESTIONS + [ML4DM_DETECTION_QUESTION]

ARXIV_TAGS = "hep-ph"
MAX_ARXIV_RESULTS = 5
MAX_EXPANSION_RESULTS = 25  # Maximum number of papers to search when expanding duplicate search

# Content processing limits
# Note: This limit applies ONLY to the extracted PDF content, not to title/abstract which are sent in full
MAX_CONTENT_LENGTH_FOR_LLM = 50000  # Maximum characters from paper content for LLM analysis (50K allows ~100% coverage for most papers)
LOG_PREVIEW_LENGTH = 500  # Length of content preview in logs
ERROR_MESSAGE_LENGTH = 100  # Length of truncated error messages

# Advanced content processing
MAX_CONCLUSIONS_LENGTH = 3000  # Maximum characters to extract from conclusions section
STRIP_REFERENCES = (
    True  # Whether to remove references/bibliography sections from all papers
)
