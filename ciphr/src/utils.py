"""
Utility functions for CIPhR workflow to eliminate code duplication.
"""

import os
import logging
import re
from .arxiv_scraper import search_arxiv
from ..config.config import MAX_EXPANSION_RESULTS


def extract_existing_arxiv_links(file_path: str) -> set[str]:
    """Extract all arXiv links from existing markdown file."""
    if not os.path.exists(file_path):
        return set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract arXiv links using regex pattern
        arxiv_pattern = r"\[Link\]\((http://arxiv\.org/abs/[^)]+)\)"
        matches = re.findall(arxiv_pattern, content)

        return set(matches)
    except Exception as e:
        logging.warning(f"Error extracting arXiv links from {file_path}: {e}")
        return set()


def extract_existing_paper_titles(file_path: str) -> set[str]:
    """Extract all paper titles from existing markdown file for more robust duplicate detection."""
    if not os.path.exists(file_path):
        return set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract titles from markdown table rows
        # Format: Title | [Link](arxiv_url) | ...

        lines = content.split("\n")
        titles = set()

        header_skipped = False
        for line in lines:
            # Skip lines that are not table rows
            if "|" not in line:
                continue

            # Skip separator lines (contain dashes)
            if "-" in line and all(c in "|-: " for c in line.strip()):
                continue

            # Skip the header row (first table row after separator)
            if not header_skipped:
                header_skipped = True
                continue

            # Split by | and get first column (title)
            parts = line.split("|")
            if len(parts) >= 2:
                title = parts[0].strip()
                if title:  # Only add non-empty titles
                    # Normalize title for comparison (strip whitespace, convert to lowercase)
                    normalized_title = title.strip().lower()
                    titles.add(normalized_title)

        return titles
    except Exception as e:
        logging.warning(f"Error extracting paper titles from {file_path}: {e}")
        return set()


def filter_new_papers(
    papers: list, existing_links: set[str], existing_titles: set[str] = None
) -> list:
    """Filter out papers that already exist in the output file based on arXiv links and titles."""
    new_papers = []
    skipped_count = 0

    if existing_titles is None:
        existing_titles = set()

    for paper in papers:
        paper_link = paper.entry_id
        paper_title_normalized = paper.title.strip().lower()

        # Check for duplicates by both arxiv link and title
        is_duplicate_link = paper_link in existing_links
        is_duplicate_title = paper_title_normalized in existing_titles

        if is_duplicate_link or is_duplicate_title:
            skipped_count += 1
            reason = "link" if is_duplicate_link else "title"
            logging.info(
                f"Skipping duplicate paper ({reason}): {paper.title} ({paper_link})"
            )
        else:
            new_papers.append(paper)

    if skipped_count > 0:
        logging.info(f"Skipped {skipped_count} duplicate papers")

    return new_papers


def apply_smart_expansion(
    papers, original_count, args, arxiv_query, existing_links, existing_titles
):
    """
    Apply smart expansion logic when all initial papers are duplicates.

    Args:
        papers: List of papers after initial filtering
        original_count: Number of papers before filtering
        args: Command line arguments
        arxiv_query: ArXiv search query string
        existing_links: Set of existing arXiv links
        existing_titles: Set of existing paper titles

    Returns:
        tuple: (filtered_papers, expansion_applied)
    """
    # Smart expansion: if all papers are duplicates, try searching more
    if len(papers) == 0 and original_count > 0:
        logging.warning(
            f"All {original_count} papers were duplicates. Expanding search to find new papers..."
        )
        expanded_results = min(
            args.max_results * 3, MAX_EXPANSION_RESULTS
        )  # Cap at config limit to avoid rate limits
        logging.info(f"Searching with expanded results: {expanded_results}")
        papers_expanded = search_arxiv(query=arxiv_query, max_results=expanded_results)
        papers = filter_new_papers(papers_expanded, existing_links, existing_titles)
        total_checked = len(papers_expanded)

        # Limit to user's original max_results to respect their intention
        if len(papers) > args.max_results:
            papers = papers[: args.max_results]
            logging.info(
                f"Expanded search: found {len(papers)} new papers after checking {total_checked} total papers (limited to user's max_results={args.max_results})"
            )
        else:
            logging.info(
                f"Expanded search: found {len(papers)} new papers after checking {total_checked} total papers"
            )

        return papers, True

    return papers, False


def setup_output_environment(args, result_processor, llm_questions):
    """
    Set up output environment including filename, append mode, and existing data extraction.

    Args:
        args: Command line arguments
        result_processor: ResultProcessor instance
        llm_questions: List of LLM questions for filename generation

    Returns:
        tuple: (final_filename, final_output_path, should_append, existing_links, existing_titles)
    """
    # Determine final output filename and check for duplicates
    final_filename = result_processor.get_output_filename(
        args.output_filename, llm_questions
    )
    final_output_path = os.path.join(args.output_dir, final_filename)
    should_append = final_filename == args.output_filename and os.path.exists(
        final_output_path
    )

    # Get existing links and titles to avoid duplicates
    existing_links = set()
    existing_titles = set()
    if should_append:
        existing_links = extract_existing_arxiv_links(final_output_path)
        existing_titles = extract_existing_paper_titles(final_output_path)
        logging.info(f"Found {len(existing_links)} existing papers in output file")

    return (
        final_filename,
        final_output_path,
        should_append,
        existing_links,
        existing_titles,
    )


def collect_and_filter_papers(args, existing_links, existing_titles):
    """
    Collect papers from arXiv and filter out duplicates with smart expansion.

    Args:
        args: Command line arguments
        existing_links: Set of existing arXiv links
        existing_titles: Set of existing paper titles

    Returns:
        list: Filtered list of new papers
    """
    logging.info(
        f"Starting data collection with tags: {args.tags}, max_results: {args.max_results}"
    )

    # Search arXiv
    arxiv_tags_formatted = args.tags.replace(",", " OR cat:")
    arxiv_query = f"cat:{arxiv_tags_formatted}"
    papers = search_arxiv(query=arxiv_query, max_results=args.max_results)

    # Filter out duplicates (by both links and titles)
    if existing_links or existing_titles:
        original_count = len(papers)
        papers = filter_new_papers(papers, existing_links, existing_titles)

        # Apply smart expansion if needed
        papers, expansion_applied = apply_smart_expansion(
            papers, original_count, args, arxiv_query, existing_links, existing_titles
        )

        if len(papers) > 0:
            if expansion_applied:
                logging.info(
                    f"Processing {len(papers)} new papers (found via smart expansion)"
                )
            else:
                logging.info(
                    f"Processing {len(papers)} new papers (filtered {original_count - len(papers)} duplicates from initial search)"
                )
        else:
            logging.info(
                f"Processing {len(papers)} new papers (filtered {original_count} duplicates)"
            )
    else:
        logging.info(f"Processing {len(papers)} papers")

    return papers


def collect_and_validate_paper_data(papers, data_processor):
    """
    Collect paper data and validate it's not empty.

    Args:
        papers: List of arXiv papers
        data_processor: DataProcessor instance

    Returns:
        list: Papers data or None if collection failed
    """
    # Collect paper data
    papers_data = data_processor.collect_paper_data(papers)

    if not papers_data:
        logging.info("No paper data collected. Exiting.")
        return None

    return papers_data


def process_and_save_results(
    papers_data, llm_results, llm_questions, result_processor, output_filename
):
    """
    Process LLM results and save final output.

    Args:
        papers_data: List of paper data dictionaries
        llm_results: List of LLM analysis results
        llm_questions: List of LLM questions
        result_processor: ResultProcessor instance
        output_filename: Output filename

    Returns:
        str: Path to saved output file
    """
    # Combine results
    combined_results = result_processor.combine_results(
        papers_data, llm_results, llm_questions
    )

    # Save final markdown
    output_file = result_processor.save_results(
        combined_results, llm_questions, output_filename
    )

    return output_file
