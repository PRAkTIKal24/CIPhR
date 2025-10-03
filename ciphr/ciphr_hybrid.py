import argparse
import json
import logging
import os
import sys

from .config.config import (
    ARXIV_TAGS,
    LLM_QUESTIONS,
    MAX_ARXIV_RESULTS,
    MAX_EXPANSION_RESULTS,
    MAX_CONTENT_LENGTH_FOR_LLM,
    LOG_PREVIEW_LENGTH,
    ERROR_MESSAGE_LENGTH,
)
from .src.arxiv_scraper import search_arxiv
from .src.data_processor import DataProcessor
from .src.llm_analyzer import LLMAnalyzer
from .src.result_processor import ResultProcessor
from .src.utils import (
    setup_output_environment,
    collect_and_filter_papers,
    collect_and_validate_paper_data,
    process_and_save_results,
)

# Constants for parsing
PAPER_SEPARATOR = "---PAPER---"

logging.basicConfig(
    filename="logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    parser = argparse.ArgumentParser(
        description="Crawl and Ingest Physics Research (CIPhR) - Data Collection Phase"
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
        help="Directory to save data files and final output (default: output)",
    )
    parser.add_argument(
        "--output_filename",
        type=str,
        default="research_insights.md",
        help="Filename for the final markdown output table (default: research_insights.md)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["collect", "process", "full", "local"],
        default="local",
        help="Mode: 'collect' (data collection only), 'process' (process existing results), 'full' (CI workflow - expects external LLM analysis), 'local' (complete local workflow with API keys)",
    )
    parser.add_argument(
        "--llm_results_file",
        type=str,
        default="llm_results.txt",
        help="File containing LLM analysis results (for process mode)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging purposes",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        # Also log to console for verbose mode
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    os.makedirs(args.output_dir, exist_ok=True)

    if args.mode in ["collect", "full"]:
        logging.info("=== DATA COLLECTION PHASE ===")

        # Initialize processors
        data_processor = DataProcessor(args.output_dir)
        result_processor = ResultProcessor(args.output_dir)

        # Set up output environment and get existing data
        final_filename, final_output_path, should_append, existing_links, existing_titles = setup_output_environment(
            args, result_processor, LLM_QUESTIONS
        )

        # Collect and filter papers with smart expansion
        papers = collect_and_filter_papers(args, existing_links if should_append else set(), existing_titles if should_append else set())

        if not papers:
            if should_append:
                logging.info("No new papers found. Nothing to process.")
            else:
                logging.info("No papers found to process.")
            return

        # Collect paper data and validate
        papers_data = collect_and_validate_paper_data(papers, data_processor)
        if not papers_data:
            return

        # Save papers data for LLM processing
        papers_data_file = data_processor.save_papers_data(
            papers_data, "papers_data.json"
        )

        # Create analysis prompts
        prompts_file = data_processor.create_analysis_prompts(
            LLM_QUESTIONS, "analysis_prompts.json"
        )

        logging.info("=== DATA COLLECTION COMPLETE ===")
        logging.info(f"Papers data saved to: {papers_data_file}")
        logging.info(f"Analysis prompts saved to: {prompts_file}")
        logging.info("Ready for LLM analysis phase")

        if args.mode == "collect":
            return

    if args.mode in ["process", "full"]:
        logging.info("=== RESULT PROCESSING PHASE ===")

        result_processor = ResultProcessor(args.output_dir)

        # Load papers data
        papers_data_file = os.path.join(args.output_dir, "papers_data.json")
        if not os.path.exists(papers_data_file):
            logging.error(f"Papers data file not found: {papers_data_file}")
            logging.error(
                "Run with --mode collect first, or ensure the data file exists."
            )
            return

        papers_data = result_processor.load_papers_data(papers_data_file)
        logging.info(f"Loaded {len(papers_data)} papers from {papers_data_file}")

        # Load LLM results
        llm_results_path = os.path.join(args.output_dir, args.llm_results_file)
        if not os.path.exists(llm_results_path):
            logging.error(f"LLM results file not found: {llm_results_path}")
            logging.error("Run the LLM analysis step first, or check the file path.")
            if args.mode == "full":
                logging.info(
                    "In 'full' mode, this would be where the GitHub Action runs run-gemini-cli"
                )
                logging.info(
                    "For now, exiting. Run the LLM analysis manually and use --mode process"
                )
            return

        # Read LLM results - expect JSON array format from run-gemini-cli
        with open(llm_results_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        logging.info(f"LLM results file size: {len(content)} characters")
        logging.info(
            f"Raw LLM results content preview: {content[:LOG_PREVIEW_LENGTH]}..."
        )

        # Handle completely empty results
        if not content:
            logging.error("LLM results file is completely empty!")
            # Create fallback results
            fallback_result = {q: "Error: Empty LLM response" for q in LLM_QUESTIONS}
            llm_results = [json.dumps(fallback_result)] * len(papers_data)
            combined_results = result_processor.combine_results(
                papers_data, llm_results, LLM_QUESTIONS
            )
            output_file = result_processor.save_results(
                combined_results, LLM_QUESTIONS, args.output_filename
            )
            logging.info(
                f"Created fallback results due to empty LLM response: {output_file}"
            )
            return

        # Parse individual results (now separated by PAPER_SEPARATOR from individual analysis)
        llm_results_parsed = []
        try:
            import re

            # First check if we have individual results separated by PAPER_SEPARATOR
            if PAPER_SEPARATOR in content:
                logging.info(
                    f"Found individual paper results separated by {PAPER_SEPARATOR}"
                )
                individual_results = content.split(PAPER_SEPARATOR)
                llm_results_parsed = [
                    result.strip() for result in individual_results if result.strip()
                ]
                logging.info(f"Split into {len(llm_results_parsed)} individual results")

            # Fallback: try to parse as JSON array (batch processing)
            elif content.strip().startswith("["):
                logging.info("Attempting to parse as JSON array (batch processing)")
                json_match = re.search(r"\[.*\]", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_data = json.loads(json_str)

                    if isinstance(parsed_data, list):
                        llm_results_parsed = [
                            json.dumps(item) if isinstance(item, dict) else str(item)
                            for item in parsed_data
                        ]
                        logging.info(
                            f"Successfully parsed {len(llm_results_parsed)} LLM results from JSON array"
                        )
                    else:
                        llm_results_parsed = [json.dumps(parsed_data)]

            # Single result case
            else:
                logging.info("Treating as single result for all papers")
                llm_results_parsed = [content]

        except (json.JSONDecodeError, AttributeError) as e:
            logging.warning(f"Could not parse LLM results as structured data: {e}")
            # Ultimate fallback - split by PAPER_SEPARATOR or use whole content
            if PAPER_SEPARATOR in content:
                llm_results_parsed = content.split(PAPER_SEPARATOR)
            else:
                llm_results_parsed = [content]

        # Final check - ensure we have the right number of results
        if len(llm_results_parsed) != len(papers_data):
            logging.warning(
                f"Final mismatch: {len(papers_data)} papers but {len(llm_results_parsed)} LLM results. Adjusting..."
            )
            if len(llm_results_parsed) < len(papers_data):
                # Pad with empty results
                while len(llm_results_parsed) < len(papers_data):
                    llm_results_parsed.append('{"error": "No LLM result available"}')
            else:
                # Truncate excess results
                llm_results_parsed = llm_results_parsed[: len(papers_data)]

        llm_results = llm_results_parsed
        logging.info(
            f"Final LLM results count: {len(llm_results)} (matching {len(papers_data)} papers)"
        )

        # Process and save results
        output_file = process_and_save_results(
            papers_data, llm_results, LLM_QUESTIONS, result_processor, args.output_filename
        )

        logging.info("=== PROCESSING COMPLETE ===")
        logging.info(f"Final results saved to: {output_file}")

    if args.mode == "local":
        logging.info("=== LOCAL MODE - COMPLETE WORKFLOW ===")

        # Initialize processors
        data_processor = DataProcessor(args.output_dir)
        result_processor = ResultProcessor(args.output_dir)
        llm_analyzer = LLMAnalyzer()

        # Set up output environment and get existing data
        final_filename, final_output_path, should_append, existing_links, existing_titles = setup_output_environment(
            args, result_processor, LLM_QUESTIONS
        )

        # Collect and filter papers with smart expansion
        papers = collect_and_filter_papers(args, existing_links if should_append else set(), existing_titles if should_append else set())

        if not papers:
            if should_append:
                logging.info("No new papers found. Nothing to process.")
            else:
                logging.info("No papers found to process.")
            return

        # Collect paper data and validate
        papers_data = collect_and_validate_paper_data(papers, data_processor)
        if not papers_data:
            return

        # Analyze papers with LLM (local API key usage)
        logging.info("=== ANALYZING PAPERS WITH LOCAL LLM ===")
        llm_results = []

        for i, paper_data in enumerate(papers_data, 1):
            logging.info(
                f"Analyzing paper {i}/{len(papers_data)}: {paper_data['title'][:50]}..."
            )

            # Create content for analysis using enhanced processing
            content = data_processor.process_content_for_llm(
                title=paper_data["title"],
                abstract=paper_data["abstract"],
                content=paper_data.get("combined_content", ""),
                max_content_length=MAX_CONTENT_LENGTH_FOR_LLM,
            )

            try:
                # Analyze with local LLM
                analysis_result = llm_analyzer.analyze_paper_with_llm(
                    content, LLM_QUESTIONS
                )

                # Convert dict result to JSON string format (to match other modes)
                if isinstance(analysis_result, dict):
                    llm_results.append(json.dumps(analysis_result))
                else:
                    llm_results.append(str(analysis_result))

                logging.info(f"Successfully analyzed paper {i}")

            except Exception as e:
                logging.error(f"Error analyzing paper {i}: {e}")
                # Create fallback result
                fallback_result = {
                    q: f"Error during analysis: {str(e)[:ERROR_MESSAGE_LENGTH]}"
                    for q in LLM_QUESTIONS
                }
                llm_results.append(json.dumps(fallback_result))

        # Process and save results using the same logic as other modes
        output_file = process_and_save_results(
            papers_data, llm_results, LLM_QUESTIONS, result_processor, args.output_filename
        )

        logging.info("=== LOCAL MODE COMPLETE ===")
        logging.info(f"Successfully processed {len(papers_data)} papers")
        logging.info(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
