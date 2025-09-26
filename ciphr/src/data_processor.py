import json
import logging
import os
from typing import Dict, List

from .arxiv_scraper import download_pdf, get_abstract_content, search_arxiv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DataProcessor:
    """Handles data collection and preparation for LLM analysis."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: str) -> str | None:
        """Extracts text from a PDF using pypdf."""
        from pypdf import PdfReader

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

    def collect_paper_data(self, papers: List) -> List[Dict]:
        """Collect and prepare paper data for LLM analysis."""
        results = []

        for i, paper in enumerate(papers):
            logging.info(f"Processing paper {i + 1}/{len(papers)}: {paper.title}")

            # Get abstract content
            abstract_content = get_abstract_content(paper)
            if not abstract_content:
                logging.warning(f"Could not get abstract for {paper.title}. Skipping.")
                continue

            # Download and extract PDF
            pdf_content = ""
            pdf_path = None
            try:
                pdf_path = download_pdf(paper, download_dir=self.output_dir)
                if pdf_path:
                    pdf_content = self.extract_text_from_pdf(pdf_path) or ""
                else:
                    logging.warning(f"Could not download PDF for {paper.title}.")
            except Exception as e:
                logging.error(f"Error processing PDF for {paper.title}: {e}")
            finally:
                # Always clean up PDF file
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    logging.info(f"Cleaned up temporary PDF: {pdf_path}")

            # Combine content
            combined_content = (
                f"Abstract Content:\n{abstract_content}\n\nPDF Content:\n{pdf_content}"
            )

            # Prepare data structure
            paper_data = {
                "title": paper.title,
                "arxiv_url": paper.entry_id,
                "abstract": abstract_content,
                "pdf_content": pdf_content,
                "combined_content": combined_content,
                "authors": [author.name for author in paper.authors],
                "published": paper.published.isoformat() if paper.published else None,
                "updated": paper.updated.isoformat() if paper.updated else None,
                "categories": paper.categories,
            }

            results.append(paper_data)

        return results

    def save_papers_data(
        self, papers_data: List[Dict], filename: str = "papers_data.json"
    ) -> str:
        """Save papers data to JSON file for LLM processing."""
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(papers_data, f, indent=2, ensure_ascii=False)

        logging.info(f"Saved {len(papers_data)} papers data to {filepath}")
        return filepath

    def create_analysis_prompts(
        self, questions: List[str], output_file: str = "analysis_prompts.json"
    ) -> str:
        """Create structured prompts for LLM analysis."""
        prompts_data = {
            "questions": questions,
            "instructions": """You are analyzing physics research papers. For each paper provided, answer the specific questions based on the paper's content.

Please respond with a JSON object where each key is the question and each value is your concise answer. Use "Not found" or "Not applicable" if the information is not available in the paper.

Example format:
{
  "What is the main physics phenomenon studied by this paper": "Dark matter direct detection",
  "Is this work related to dark matter searches? If yes, how?": "Yes, this paper presents results from the XENON experiment searching for WIMP dark matter",
  "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?": "Yes, XENON detector"
}""",
        }

        filepath = os.path.join(self.output_dir, output_file)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(prompts_data, f, indent=2, ensure_ascii=False)

        logging.info(f"Created analysis prompts file: {filepath}")
        return filepath


if __name__ == "__main__":
    # Test the data processor
    processor = DataProcessor()
    papers = search_arxiv("cat:hep-ex", max_results=2)
    if papers:
        papers_data = processor.collect_paper_data(papers)
        processor.save_papers_data(papers_data)
        print(f"Processed {len(papers_data)} papers")
