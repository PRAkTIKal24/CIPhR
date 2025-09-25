import argparse
import logging
import os
import re
from datetime import datetime

from .config.config import ARXIV_TAGS, LLM_QUESTIONS, MAX_ARXIV_RESULTS
from .src.arxiv_scraper import (  # Changed import
    download_pdf,
    get_abstract_content,
    search_arxiv,
)
from .src.llm_analyzer import LLMAnalyzer

logging.basicConfig(
    filename="logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def extract_questions_from_existing_file(file_path: str) -> list[str]:
    """Extract LLM questions from existing markdown file by parsing the header row."""
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if len(lines) < 1:
            return []
        
        # Parse the header row (first line)
        header_line = lines[0].strip()
        headers = [h.strip() for h in header_line.split("|")]
        
        # Remove "Paper Title" and "arXiv Link" to get only LLM questions
        if len(headers) >= 2:
            llm_questions = headers[2:]  # Skip first two columns
            return [q for q in llm_questions if q]  # Remove empty strings
        
        return []
    except Exception as e:
        logging.warning(f"Error extracting questions from {file_path}: {e}")
        return []


def questions_match(existing_questions: list[str], config_questions: list[str]) -> bool:
    """Check if existing file questions exactly match config questions."""
    # Normalize questions by removing newlines and extra spaces
    existing_normalized = [q.replace("\n", " ").strip() for q in existing_questions]
    config_normalized = [q.replace("\n", " ").strip() for q in config_questions]
    
    return existing_normalized == config_normalized


def generate_date_suffix() -> str:
    """Generate date suffix in ddmmyy format."""
    now = datetime.now()
    return now.strftime("%d%m%y")


def extract_existing_arxiv_links(file_path: str) -> set[str]:
    """Extract all arXiv links from existing markdown file."""
    if not os.path.exists(file_path):
        return set()
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract arXiv links using regex pattern
        # Look for markdown links in the format [Link](http://arxiv.org/abs/...)
        import re
        arxiv_pattern = r'\[Link\]\((http://arxiv\.org/abs/[^)]+)\)'
        matches = re.findall(arxiv_pattern, content)
        
        return set(matches)
    except Exception as e:
        logging.warning(f"Error extracting arXiv links from {file_path}: {e}")
        return set()


def filter_new_papers(papers: list, existing_links: set[str]) -> list:
    """Filter out papers that already exist in the output file based on arXiv links."""
    new_papers = []
    skipped_count = 0
    
    for paper in papers:
        paper_link = paper.entry_id
        if paper_link not in existing_links:
            new_papers.append(paper)
        else:
            skipped_count += 1
            logging.info(f"Skipping duplicate paper: {paper.title} ({paper_link})")
    
    if skipped_count > 0:
        logging.info(f"Skipped {skipped_count} duplicate papers")
    
    return new_papers


def get_output_filename(base_filename: str, output_dir: str) -> str:
    """
    Determine the appropriate output filename based on existing file and question matching.
    Returns either the original filename or a new filename with date suffix.
    """
    output_path = os.path.join(output_dir, base_filename)
    
    # Check if file exists
    if not os.path.exists(output_path):
        return base_filename
    
    # Extract questions from existing file
    existing_questions = extract_questions_from_existing_file(output_path)
    
    # Check if questions match
    if questions_match(existing_questions, LLM_QUESTIONS):
        return base_filename  # Use original filename for appending
    
    # Create new filename with date suffix
    name, ext = os.path.splitext(base_filename)
    date_suffix = generate_date_suffix()
    return f"{name}_{date_suffix}{ext}"


def generate_markdown_table(results: list[dict], include_header: bool = True) -> str:
    """Generates a markdown table from the analysis results."""
    if not results:
        return "No results to display."

    markdown = ""
    
    if include_header:
        # Prepare headers
        headers = ["Paper Title", "arXiv Link"] + [
            q.replace("\n", " ") for q in LLM_QUESTIONS
        ]
        markdown += " | ".join(headers) + "\n"
        markdown += " | ".join(["-" * len(h) for h in headers]) + "\n"

    # Add rows
    for res in results:
        row = [res["title"], f"[Link]({res['arxiv_url']})"]
        for q in LLM_QUESTIONS:
            answer = res["llm_answers"].get(q, "N/A")
            # Replace newlines in answers for single-line table cells
            row.append(answer.replace("\n", " "))
        markdown += " | ".join(row) + "\n"
    return markdown


def main():
    parser = argparse.ArgumentParser(
        description="Crawl and Ingest Physics Research (CIPhR)"
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=ARXIV_TAGS,
        help=f"Comma-separated arXiv categories/tags (e.g., {ARXIV_TAGS})",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        default=MAX_ARXIV_RESULTS,
        help=f"Maximum number of arXiv papers to process (default: {MAX_ARXIV_RESULTS})",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Directory to save downloaded PDFs and output table (default: output)",
    )
    parser.add_argument(
        "--output_filename",
        type=str,
        default="research_insights.md",
        help="Filename for the markdown output table (default: research_insights.md)",
    )
    # add argument for verbosity
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging purposes",
    )

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    
    # Determine the appropriate output filename
    actual_filename = get_output_filename(args.output_filename, args.output_dir)
    output_path = os.path.join(args.output_dir, actual_filename)
    
    # Check if we should append to existing file
    should_append = (actual_filename == args.output_filename and 
                     os.path.exists(output_path))
    
    # Get existing arXiv links to avoid duplicates
    existing_links = set()
    if should_append:
        existing_links = extract_existing_arxiv_links(output_path)
        logging.info(f"Found {len(existing_links)} existing papers in output file")

    logging.info(
        f"Starting CIPhR with tags: {args.tags}, max_results: {args.max_results}"
    )

    # Initialize LLM Analyzer
    llm_analyzer = LLMAnalyzer()

    all_results = []
    arxiv_tags_formatted = args.tags.replace(",", " OR cat:")
    arxiv_query = f"cat:{arxiv_tags_formatted}"
    papers = search_arxiv(query=arxiv_query, max_results=args.max_results)
    
    # Filter out papers that already exist in the output file
    if should_append and existing_links:
        original_count = len(papers)
        papers = filter_new_papers(papers, existing_links)
        logging.info(f"Processing {len(papers)} new papers (filtered {original_count - len(papers)} duplicates)")
    else:
        logging.info(f"Processing {len(papers)} papers")

    for paper in papers:
        logging.info(f"Processing paper: {paper.title}")
        result_entry = {
            "title": paper.title,
            "arxiv_url": paper.entry_id,
            "llm_answers": {},
        }

        # 1. Get abstract content directly from arxiv.Result
        abstract_content = get_abstract_content(paper)
        if not abstract_content:
            logging.warning(
                f"Could not get abstract for {paper.title}. Skipping LLM analysis."
            )
            all_results.append(result_entry)
            continue

        # 2. Download PDF and extract text
        pdf_path = None
        try:
            pdf_path = download_pdf(paper, download_dir=args.output_dir)
            pdf_content = ""
            if pdf_path:
                pdf_content = llm_analyzer.extract_text_from_pdf(pdf_path) or ""
            else:
                logging.warning(
                    f"Could not download PDF for {paper.title}. LLM analysis will only use abstract content."
                )

            # Combine contents
            combined_content = (
                f"Abstract Content:\n{abstract_content}\n\nPDF Content:\n{pdf_content}"
            )

            # 3. Analyze with LLM
            if combined_content.strip():
                llm_answers = llm_analyzer.analyze_paper_with_llm(
                    combined_content, LLM_QUESTIONS
                )
                result_entry["llm_answers"] = llm_answers
            else:
                logging.warning(
                    f"No content available for LLM analysis for {paper.title}."
                )

        finally:
            # Delete PDF after processing
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
                logging.info(f"Deleted temporary PDF: {pdf_path}")

        all_results.append(result_entry)

    # Generate and save markdown table
    if not all_results:
        if should_append:
            logging.info("No new papers found. Nothing to append.")
        else:
            logging.info("No papers found to process.")
        return
    
    if should_append:
        # Append mode: don't include header, just add new rows
        markdown_table = generate_markdown_table(all_results, include_header=False)
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(markdown_table)
        logging.info(f"Analysis complete. {len(all_results)} new results appended to existing file: {output_path}")
    else:
        # New file mode: include full table with header
        markdown_table = generate_markdown_table(all_results, include_header=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_table)
        if actual_filename != args.output_filename:
            logging.info(f"Analysis complete. New file created with date suffix: {output_path}")
        else:
            logging.info(f"Analysis complete. Markdown table saved to {output_path}")


if __name__ == "__main__":
    main()
