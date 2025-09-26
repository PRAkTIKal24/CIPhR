import logging
import os  # noqa: F401

import google.generativeai as genai
from firecrawl import FirecrawlApp
from pypdf import PdfReader

from ..config.config import (  # noqa: F401
    FIRECRAWL_API_KEY,
    GEMINI_API_KEY,
    LLM_QUESTIONS,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class LLMAnalyzer:
    def __init__(self):
        if not FIRECRAWL_API_KEY:
            logging.error("FIRECRAWL_API_KEY not found in environment variables.")
            raise ValueError("FIRECRAWL_API_KEY is required.")
        if not GEMINI_API_KEY:
            logging.error("GEMINI_API_KEY not found in environment variables.")
            raise ValueError("GEMINI_API_KEY is required.")

        self.firecrawl_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        
        # Configure to use Google AI API explicitly, not Vertex AI
        # Prevent auto-detection of GCP environment that leads to Vertex AI usage
        os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE'] = 'false'
        os.environ['GOOGLE_CLOUD_PROJECT'] = ''  # Clear any GCP project detection
        
        # Clear any potential Vertex AI environment variables
        for env_var in ['GOOGLE_APPLICATION_CREDENTIALS', 'GCLOUD_PROJECT']:
            if env_var in os.environ:
                del os.environ[env_var]
        
        genai.configure(
            api_key=GEMINI_API_KEY,
            transport='rest'  # Force REST API instead of gRPC to avoid Vertex AI detection
        )
        
        logging.info("Google AI configured with REST transport to avoid Vertex AI detection")
        
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )  # Using 1.5 Flash as requested

    def extract_text_from_pdf(self, pdf_path: str) -> str | None:
        """Extracts text from a PDF using pypdf."""
        logging.info(f"Extracting text from PDF: {pdf_path} using pypdf.")
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            logging.info(f"Successfully extracted text from {pdf_path}")
            return text
        except Exception as e:
            logging.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return None

    def analyze_paper_with_llm(
        self, combined_content: str, questions: list[str]
    ) -> dict:
        """Analyzes combined paper content (abstract + PDF) with LLM to answer specific questions."""
        logging.info("Analyzing paper content with LLM.")
        answers = {}
        for question in questions:
            prompt = f"""Based on the following research paper content, answer the question concisely:

Paper Content:
{combined_content}

Question: {question}

Answer:"""
            try:
                logging.debug(f"Attempting to generate content for question: {question}")
                response = self.model.generate_content(prompt)
                answers[question] = response.text.strip()
                logging.info(f"Answered question: {question}")
            except Exception as e:
                logging.error(
                    f"Error analyzing paper with LLM for question '{question}': {e}"
                )
                logging.error(f"Error type: {type(e).__name__}")
                if hasattr(e, 'code'):
                    logging.error(f"Error code: {e.code}")
                answers[question] = "Error or not found."
        return answers


if __name__ == "__main__":
    pass
