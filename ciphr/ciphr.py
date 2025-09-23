import argparse
import logging
import os
from datetime import datetime  # noqa: F401

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


def generate_markdown_table(results: list[dict]) -> str:
    """Generates a markdown table from the analysis results."""
    if not results:
        return "No results to display."

    # Prepare headers
    headers = ["Paper Title", "arXiv Link"] + [
        q.replace("\n", " ") for q in LLM_QUESTIONS
    ]
    markdown = " | ".join(headers) + "\n"
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

    output_path = os.path.join(args.output_dir, args.output_filename)
    os.makedirs(args.output_dir, exist_ok=True)

    logging.info(
        f"Starting CIPhR with tags: {args.tags}, max_results: {args.max_results}"
    )

    # Initialize LLM Analyzer
    llm_analyzer = LLMAnalyzer()

    all_results = []
    arxiv_tags_formatted = args.tags.replace(",", " OR cat:")
    arxiv_query = f"cat:{arxiv_tags_formatted}"
    papers = search_arxiv(query=arxiv_query, max_results=args.max_results)

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
    markdown_table = generate_markdown_table(all_results)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_table)
    logging.info(f"Analysis complete. Markdown table saved to {output_path}")


if __name__ == "__main__":
    main()
