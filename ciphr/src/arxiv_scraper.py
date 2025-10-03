import logging
import os

import arxiv
from firecrawl import FirecrawlApp  # noqa: F401

from ..config.config import FIRECRAWL_API_KEY  # noqa: F401

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def search_arxiv(query: str, max_results: int = 10):
    """Searches arXiv for papers based on a query and returns a list of results."""
    logging.info(f"Searching arXiv for query: {query} with max_results: {max_results}")
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        results = list(search.results())
        logging.info(f"Found {len(results)} results for query: {query}")
        
        # Log the dates of the first few papers for debugging
        if results:
            for i, paper in enumerate(results[:min(3, len(results))]):
                submitted_date = paper.published.strftime("%Y-%m-%d") if paper.published else "Unknown"
                arxiv_id = paper.entry_id.split('/')[-1]
                logging.info(f"Paper {i+1}: {arxiv_id} (submitted: {submitted_date})")
        
        return results
    except Exception as e:
        logging.error(f"Error searching arXiv: {e}")
        return []


def download_pdf(paper: arxiv.Result, download_dir: str = "data") -> str | None:
    """Downloads the PDF of a given arXiv paper."""
    os.makedirs(download_dir, exist_ok=True)
    try:
        filename = f"{paper.entry_id.split('/')[-1]}.pdf"
        filepath = os.path.join(download_dir, filename)
        logging.info(f"Attempting to download PDF for {paper.title} to {filepath}")
        paper.download_pdf(dirpath=download_dir, filename=filename)
        logging.info(f"Successfully downloaded {paper.title} to {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error downloading PDF for {paper.title}: {e}")
        return None


def get_abstract_content(paper: arxiv.Result) -> str:
    """Returns the abstract content directly from the arxiv.Result object."""
    logging.info(f"Extracting abstract from arxiv.Result for {paper.title}")
    return paper.summary


if __name__ == "__main__":
    # Example usage
    query = 'cat:hep-ph AND ti:"dark matter"'
    papers = search_arxiv(query=query, max_results=2)
    for paper in papers:
        print(f"Title: {paper.title}")
        print(f"Authors: {[author.name for author in paper.authors]}")
        print(f"URL: {paper.entry_id}")
        download_path = download_pdf(paper)
        if download_path:
            print(f"Downloaded to: {download_path}")

        abstract_content = get_abstract_content(paper)
        if abstract_content:
            print(f"Abstract Content (first 200 chars): {abstract_content[:200]}...")
        print("---")
