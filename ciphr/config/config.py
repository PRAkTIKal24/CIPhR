import os

from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

LLM_QUESTIONS = [
    "What is the main physics phenomenon studied by this paper",
    "When was this paper published on arxiv?",
    "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?",
]

ARXIV_TAGS = "hep-ph"
MAX_ARXIV_RESULTS = 5
