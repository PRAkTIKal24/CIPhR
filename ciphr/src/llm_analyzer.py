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
        genai.configure(api_key=GEMINI_API_KEY)
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
                response = self.model.generate_content(prompt)
                answers[question] = response.text.strip()
                logging.info(f"Answered question: {question}")
            except Exception as e:
                logging.error(
                    f"Error analyzing paper with LLM for question '{question}': {e}"
                )
                answers[question] = "Error or not found."
        return answers


if __name__ == "__main__":
    pass
