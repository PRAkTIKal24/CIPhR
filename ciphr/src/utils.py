"""
Utility functions for CIPhR workflow to eliminate code duplication.
"""
import os
import logging
import re
from .data_processor import DataProcessor
from .result_processor import ResultProcessor
from .arxiv_scraper import search_arxiv
from ..config.config import MAX_EXPANSION_RESULTS


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

    return final_filename, final_output_path, should_append, existing_links, existing_titles


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
                logging.info(f"Processing {len(papers)} new papers (found via smart expansion)")
            else:
                logging.info(
                    f"Processing {len(papers)} new papers (filtered {original_count - len(papers)} duplicates from initial search)"
                )
        else:
            logging.info(f"Processing {len(papers)} new papers (filtered {original_count} duplicates)")
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


def process_and_save_results(papers_data, llm_results, llm_questions, result_processor, output_filename):
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