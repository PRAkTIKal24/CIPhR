import json
import logging
import os
import re
from typing import Dict, List, Optional

from .arxiv_scraper import download_pdf, get_abstract_content, search_arxiv
from ..config.config import STRIP_REFERENCES, MAX_CONCLUSIONS_LENGTH

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

            # Combine content and strip references
            raw_combined_content = (
                f"Abstract Content:\n{abstract_content}\n\nPDF Content:\n{pdf_content}"
            )
            combined_content = self.strip_references_section(raw_combined_content)

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

    def strip_references_section(self, text: str) -> str:
        """Remove references/bibliography sections from paper text."""
        if not STRIP_REFERENCES:
            return text

        # Common reference section patterns (case-insensitive)
        ref_patterns = [
            r"\n\s*REFERENCES\s*\n",
            r"\n\s*References\s*\n",
            r"\n\s*BIBLIOGRAPHY\s*\n",
            r"\n\s*Bibliography\s*\n",
            r"\n\s*REFERENCE LIST\s*\n",
            r"\n\s*Reference List\s*\n",
        ]

        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Return text up to the reference section
                ref_start = match.start()
                stripped_text = text[:ref_start].strip()
                logging.debug(
                    f"Stripped references section. Original: {len(text)} chars, After: {len(stripped_text)} chars"
                )
                return stripped_text

        return text

    def extract_conclusions_section(self, text: str) -> Optional[str]:
        """Extract conclusions section from paper text."""
        # Common conclusion section patterns (case-insensitive, with optional numbering)
        conclusion_patterns = [
            r"\n\s*(?:\d+\.?\s+)?(Conclusions?):?\s*\n",
            r"\n\s*(?:\d+\.?\s+)?(Discussion(?:s?(?:\s+and\s+Conclusions?)?)?):?\s*\n",
            r"\n\s*(?:\d+\.?\s+)?(Summary(?:\s+and\s+Conclusions?)?):?\s*\n",
            r"\n\s*(?:\d+\.?\s+)?(Concluding\s+Remarks?):?\s*\n",
            r"\n\s*(?:\d+\.?\s+)?(Final\s+Remarks?):?\s*\n",
            r"\n\s*(?:\d+\.?\s+)?(Results?\s+and\s+Discussions?):?\s*\n",
            r"\n\s*(?:\d+\.?\s+)?(Outlook):?\s*\n",
        ]

        for pattern in conclusion_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                section_start = match.end()

                # Find the end of the section (next section header or end of text)
                # Look for next numbered section or end
                next_section_patterns = [
                    r"\n\s*\d+\.?\s+[A-Z][^.\n]*\n",  # Next numbered section
                    r"\n\s*(?:REFERENCES?|BIBLIOGRAPHY|ACKNOWLEDGMENTS?|APPENDIX)\s*\n",  # Special sections
                ]

                section_end = len(text)  # Default to end of text
                for next_pattern in next_section_patterns:
                    next_match = re.search(
                        next_pattern, text[section_start:], re.IGNORECASE
                    )
                    if next_match:
                        section_end = section_start + next_match.start()
                        break

                # Extract and clean the conclusions section
                conclusions = text[section_start:section_end].strip()

                # Limit length
                if len(conclusions) > MAX_CONCLUSIONS_LENGTH:
                    conclusions = conclusions[:MAX_CONCLUSIONS_LENGTH] + "..."

                if conclusions:
                    section_name = match.group(1)
                    logging.debug(
                        f"Extracted {section_name} section: {len(conclusions)} chars"
                    )
                    return conclusions

        return None

    def process_content_for_llm(
        self, title: str, abstract: str, content: str, max_content_length: int
    ) -> str:
        """
        Process and organize content for LLM analysis.

        For papers exceeding max_content_length:
        - Order: Title -> Abstract -> Conclusions -> Main Content (truncated)

        For papers within limit:
        - Order: Title -> Abstract -> Main Content (full, already includes conclusions)
        """
        # Always strip references first
        content_no_refs = self.strip_references_section(content)

        # Check if we need special processing (content exceeds limit)
        if len(content_no_refs) > max_content_length:
            # Extract conclusions before truncating
            conclusions = self.extract_conclusions_section(content_no_refs)

            if conclusions:
                # Calculate remaining space for main content
                conclusions_header = "\n\n[CONCLUSIONS SECTION]:\n"
                conclusions_content = conclusions_header + conclusions
                remaining_space = max_content_length - len(conclusions_content)

                # Truncate main content to fit
                main_content = content_no_refs[: max(0, remaining_space)]

                # Assemble final content: Title + Abstract + Conclusions + Main Content
                processed_content = f"Title: {title}\n\nAbstract: {abstract}{conclusions_content}\n\n[MAIN CONTENT]:\n{main_content}"

                logging.info(
                    f"Long paper processing: Main content {len(main_content)} chars + Conclusions {len(conclusions)} chars"
                )
            else:
                # No conclusions found, just truncate
                main_content = content_no_refs[:max_content_length]
                processed_content = (
                    f"Title: {title}\n\nAbstract: {abstract}\n\nContent: {main_content}"
                )

                logging.debug("No conclusions section found, using standard truncation")
        else:
            # Paper fits within limit, use standard format
            processed_content = (
                f"Title: {title}\n\nAbstract: {abstract}\n\nContent: {content_no_refs}"
            )
            logging.debug(
                f"Standard processing: Content fits within {max_content_length} char limit"
            )

        return processed_content


if __name__ == "__main__":
    # Test the data processor
    processor = DataProcessor()
    papers = search_arxiv("cat:hep-ex", max_results=2)
    if papers:
        papers_data = processor.collect_paper_data(papers)
        processor.save_papers_data(papers_data)
        print(f"Processed {len(papers_data)} papers")
