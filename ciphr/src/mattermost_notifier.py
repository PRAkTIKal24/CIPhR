import json
import logging
import os
import requests
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MattermostNotifier:
    """Handles posting messages to Mattermost via incoming webhooks."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def post_ml4dm_findings(self, ml4dm_papers: List[Dict], repo_link: str) -> bool:
        """
        Post ML4DM findings to Mattermost channel.

        Args:
            ml4dm_papers: List of papers that use ML for dark matter research
            repo_link: Link to the full output table in the repository

        Returns:
            bool: True if message was posted successfully, False otherwise
        """
        if not ml4dm_papers:
            logging.info("No ML4DM papers found, skipping Mattermost post")
            return True

        try:
            # Create the message
            message = self._format_ml4dm_message(ml4dm_papers, repo_link)

            # Prepare payload
            payload = {
                "text": message,
                "username": "CIPhR Bot",
                "icon_emoji": ":robot_face:",
            }

            # Send to Mattermost
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                logging.info(
                    f"Successfully posted ML4DM findings to Mattermost. Found {len(ml4dm_papers)} papers."
                )
                return True
            else:
                logging.error(
                    f"Failed to post to Mattermost. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            logging.error(f"Error posting to Mattermost: {e}")
            return False

    def _format_ml4dm_message(self, ml4dm_papers: List[Dict], repo_link: str) -> str:
        """
        Format the Mattermost message with ML4DM papers.

        Args:
            ml4dm_papers: List of papers that use ML for dark matter research
            repo_link: Link to the full output table

        Returns:
            str: Formatted message for Mattermost
        """
        # Header with emojis
        count = len(ml4dm_papers)
        header = f"🚀 🤖 New ML4DM papers on arXiv today! Found {count} paper{'s' if count != 1 else ''} using ML techniques for dark matter searches.\n\n"

        # Create mini markdown table
        table_header = "| Paper Title | arXiv Link | ML Techniques |\n|---|---|---|\n"

        table_rows = ""
        for paper in ml4dm_papers:
            title = paper["title"]
            arxiv_url = paper["arxiv_url"]
            ml_answer = paper.get("ml4dm_answer", "N/A")

            # Truncate title if too long for better formatting
            if len(title) > 60:
                title = title[:60] + "..."

            # Extract just the ML techniques part if the answer is verbose
            ml_techniques = self._extract_ml_techniques(ml_answer)

            table_rows += f"| {title} | [Link]({arxiv_url}) | {ml_techniques} |\n"

        # Footer with link to full table
        footer = f"\n📊 [View full analysis table here]({repo_link})"

        return header + table_header + table_rows + footer

    def _extract_ml_techniques(self, ml_answer: str) -> str:
        """
        Extract ML techniques from the LLM answer.

        Args:
            ml_answer: The full LLM answer about ML techniques

        Returns:
            str: Cleaned up ML techniques description
        """
        # If the answer starts with "Yes" or similar, try to extract the techniques part
        if ml_answer.lower().startswith(("yes", "this paper")):
            # Look for patterns that indicate the techniques list
            for delimiter in [
                ". The main ML techniques",
                ": ",
                ". Techniques",
                ". Methods",
            ]:
                if delimiter in ml_answer:
                    techniques_part = ml_answer.split(delimiter, 1)[1]
                    # Clean up and truncate if needed
                    techniques_part = techniques_part.strip()
                    if len(techniques_part) > 100:
                        techniques_part = techniques_part[:100] + "..."
                    return techniques_part

        # If no pattern found, return the whole answer but truncated
        if len(ml_answer) > 100:
            return ml_answer[:100] + "..."

        return ml_answer


def check_ml4dm_papers(papers_data: List[Dict], llm_results: List[str]) -> List[Dict]:
    """
    Check which papers use ML for dark matter research.

    Args:
        papers_data: List of paper data dictionaries
        llm_results: List of LLM analysis results

    Returns:
        List[Dict]: Papers that use ML for dark matter research
    """
    ml4dm_papers = []
    ml4dm_question = "Does this paper use ML techniques for dark matter searches? And if yes, list the main ML techniques used in this paper"

    for i, (paper_data, llm_result) in enumerate(
        zip(papers_data, llm_results, strict=True)
    ):
        try:
            # Parse LLM result as JSON
            if isinstance(llm_result, str):
                # Try to extract JSON from the result
                import re

                json_match = re.search(r"\{.*\}", llm_result, re.DOTALL)
                if json_match:
                    llm_json = json.loads(json_match.group())
                else:
                    logging.warning(
                        f"Could not extract JSON from LLM result for paper {i + 1}"
                    )
                    continue
            else:
                llm_json = llm_result

            # Get the ML4DM answer
            ml4dm_answer = llm_json.get(ml4dm_question, "").strip()

            # Check if the answer indicates ML usage
            if _indicates_ml_usage(ml4dm_answer):
                ml4dm_paper = {
                    "title": paper_data["title"],
                    "arxiv_url": paper_data["arxiv_url"],
                    "ml4dm_answer": ml4dm_answer,
                    "metadata": paper_data.get("metadata", {}),
                }
                ml4dm_papers.append(ml4dm_paper)
                logging.info(
                    f"Paper {i + 1} flagged as ML4DM: {paper_data['title'][:50]}..."
                )

        except Exception as e:
            logging.warning(f"Error processing paper {i + 1} for ML4DM check: {e}")
            continue

    return ml4dm_papers


def _indicates_ml_usage(answer: str) -> bool:
    """
    Check if the LLM answer indicates ML usage for dark matter research.

    Args:
        answer: The LLM answer to analyze

    Returns:
        bool: True if the answer indicates ML usage, False otherwise
    """
    if not answer or answer.lower() in ["n/a", "not found", "error"]:
        return False

    answer_lower = answer.lower()

    # Strong positive indicators
    positive_indicators = [
        "yes",
        "but",
        "neural network",
        "deep learning",
        "artificial intelligence",
        "classification",
        "regression",
        "clustering",
        "random forest",
        "support vector",
        "gradient boosting",
        "convolutional",
        "transformer",
        "autoencoder",
        "graph",
        "decision tree",
    ]

    # Strong negative indicators
    negative_indicators = [
        "no",
        "does not use",
        "does not mention",
        "no, this paper does not",
        "this paper does not use",
        "no machine learning",
    ]

    # Check for negative indicators first
    for neg_indicator in negative_indicators:
        if neg_indicator in answer_lower:
            return False

    # Check for positive indicators
    for pos_indicator in positive_indicators:
        if pos_indicator in answer_lower:
            return True

    return False


if __name__ == "__main__":
    # Test the notifier
    test_papers = [
        {
            "title": "Test ML Paper for Dark Matter Detection",
            "arxiv_url": "http://arxiv.org/abs/test123",
            "ml4dm_answer": "Yes, this paper uses neural networks and random forest algorithms for dark matter detection.",
            "metadata": {},
        }
    ]

    # This would use a test webhook URL
    webhook_url = os.getenv("MM_WEBHOOK_URL", "test_url")
    notifier = MattermostNotifier(webhook_url)

    # Test message formatting
    message = notifier._format_ml4dm_message(
        test_papers, "https://github.com/test/repo"
    )
    print("Test message:")
    print(message)
