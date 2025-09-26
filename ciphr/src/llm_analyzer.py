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
        os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
        os.environ["GOOGLE_CLOUD_PROJECT"] = ""  # Clear any GCP project detection

        # Clear any potential Vertex AI environment variables
        for env_var in ["GOOGLE_APPLICATION_CREDENTIALS", "GCLOUD_PROJECT"]:
            if env_var in os.environ:
                logging.info(f"Clearing environment variable: {env_var}")
                del os.environ[env_var]

        # Additional environment variables to prevent Vertex AI detection
        os.environ["GOOGLE_AI_STUDIO"] = "true"  # Indicate we want AI Studio API

        logging.info("Configuring Google AI with API key authentication")
        logging.info(f"API key present: {bool(GEMINI_API_KEY)}")
        logging.info(
            f"API key prefix: {GEMINI_API_KEY[:10] if GEMINI_API_KEY else 'None'}..."
        )

        # Try to configure with minimal options first
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            logging.info("Google AI configured successfully with API key only")
        except Exception as e:
            logging.warning(f"Basic configuration failed: {e}")
            # Fallback to explicit transport configuration
            genai.configure(api_key=GEMINI_API_KEY, transport="rest")
            logging.info("Google AI configured with REST transport as fallback")

        # First try to list available models to see what's actually available
        try:
            available_models = list(genai.list_models())
            logging.info(f"Found {len(available_models)} available models")
            model_names = [
                model.name
                for model in available_models
                if "gemini" in model.name.lower()
            ]
            logging.info(f"Available Gemini models: {model_names[:3]}")  # Log first 3
        except Exception as e:
            logging.warning(f"Could not list available models: {e}")
            model_names = []

        # Try multiple model names in order of preference
        model_names_to_try = [
            "gemini-1.5-flash",  # Original model name (should work)
            "gemini-pro",  # Stable model
            "gemini-1.5-flash-001",  # Specific version
            "models/gemini-1.5-flash",  # With models/ prefix
        ]

        # If we got available models from the API, try those first
        if model_names:
            # Prefer flash models, then pro models
            preferred_models = [name for name in model_names if "flash" in name.lower()]
            preferred_models.extend(
                [name for name in model_names if "pro" in name.lower()]
            )
            model_names_to_try = preferred_models[:2] + model_names_to_try

        self.model = None
        for model_name in model_names_to_try:
            try:
                logging.info(f"Trying to initialize model: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                logging.info(f"Successfully initialized model: {model_name}")
                break
            except Exception as e:
                logging.warning(f"Failed to initialize model {model_name}: {e}")
                continue

        if self.model is None:
            raise ValueError("Failed to initialize any Gemini model")

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
                logging.debug(
                    f"Attempting to generate content for question: {question}"
                )
                logging.debug(
                    f"Using model: {self.model._model_name if hasattr(self.model, '_model_name') else 'unknown'}"
                )
                response = self.model.generate_content(prompt)
                answers[question] = response.text.strip()
                logging.info(f"Answered question: {question}")
            except Exception as e:
                logging.error(
                    f"Error analyzing paper with LLM for question '{question}': {e}"
                )
                logging.error(f"Error type: {type(e).__name__}")
                if hasattr(e, "code"):
                    logging.error(f"Error code: {e.code}")
                if hasattr(e, "details"):
                    logging.error(f"Error details: {e.details}")
                # Log the full error for debugging
                import traceback

                logging.error(f"Full traceback: {traceback.format_exc()}")
                answers[question] = "Error or not found."
        return answers


if __name__ == "__main__":
    pass
