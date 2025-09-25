"""
Integration test to demonstrate the complete append functionality workflow.
This test creates mock scenarios and validates the behavior.
"""

import os
import tempfile

from ciphr.ciphr import (
    generate_date_suffix,
    get_output_filename,
    generate_markdown_table,
    extract_existing_arxiv_links,
    filter_new_papers,
)
from ciphr.config.config import LLM_QUESTIONS


def test_complete_append_workflow():
    """Test the complete workflow with temporary files."""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n=== Testing Complete Workflow in {temp_dir} ===")

        # Mock results for testing
        mock_results = [
            {
                "title": "Dark Matter Detection with XENON",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "llm_answers": {
                    LLM_QUESTIONS[0]: "Dark matter direct detection",
                    LLM_QUESTIONS[
                        1
                    ]: "Yes, searching for WIMP dark matter interactions",
                    LLM_QUESTIONS[2]: "Yes, XENON detector",
                },
            }
        ]

        # Scenario 1: New file creation
        print("\n--- Scenario 1: Creating new file ---")
        filename1 = get_output_filename("physics_papers.md", temp_dir)
        output_path1 = os.path.join(temp_dir, filename1)
        should_append1 = filename1 == "physics_papers.md" and os.path.exists(
            output_path1
        )

        print(f"Filename: {filename1}")
        print(f"Should append: {should_append1}")

        # Create the file
        markdown_content = generate_markdown_table(mock_results, include_header=True)
        with open(output_path1, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Created file: {output_path1}")
        print("File contents:")
        with open(output_path1, "r", encoding="utf-8") as f:
            print(f.read())

        # Scenario 2: Appending to existing file with same questions
        print("\n--- Scenario 2: Appending to existing file ---")
        filename2 = get_output_filename("physics_papers.md", temp_dir)
        output_path2 = os.path.join(temp_dir, filename2)
        should_append2 = filename2 == "physics_papers.md" and os.path.exists(
            output_path2
        )

        print(f"Filename: {filename2}")
        print(f"Should append: {should_append2}")

        if should_append2:
            # Add new results (append mode)
            new_mock_results = [
                {
                    "title": "Higgs Boson Properties",
                    "arxiv_url": "http://arxiv.org/abs/2024.67890",
                    "llm_answers": {
                        LLM_QUESTIONS[0]: "Higgs boson physics",
                        LLM_QUESTIONS[1]: "No, standard model particle physics",
                        LLM_QUESTIONS[2]: "Yes, CMS detector",
                    },
                }
            ]

            markdown_append = generate_markdown_table(
                new_mock_results, include_header=False
            )
            with open(output_path2, "a", encoding="utf-8") as f:
                f.write(markdown_append)

            print("Appended to file. Updated contents:")
            with open(output_path2, "r", encoding="utf-8") as f:
                print(f.read())

        # Scenario 3: Creating file with different questions (simulate config change)
        print("\n--- Scenario 3: Creating file with different questions ---")

        # Create a file with different questions to simulate config change
        different_questions_file = os.path.join(temp_dir, "different_questions.md")
        different_content = """Paper Title | arXiv Link | Different Question 1 | Different Question 2
----------- | ---------- | -------------------- | --------------------
Some Paper | [Link](http://arxiv.org/abs/test) | Answer 1 | Answer 2
"""

        with open(different_questions_file, "w", encoding="utf-8") as f:
            f.write(different_content)

        # Test filename generation for this file
        filename3 = get_output_filename("different_questions.md", temp_dir)
        print(f"Filename for file with different questions: {filename3}")

        # Should create new file with date suffix since questions don't match
        expected_suffix = generate_date_suffix()
        expected_filename = f"different_questions_{expected_suffix}.md"
        assert filename3 == expected_filename, (
            f"Expected {expected_filename}, got {filename3}"
        )

        print(f"✓ Correctly generated filename with date suffix: {filename3}")

        # Scenario 4: Testing duplicate detection
        print("\n--- Scenario 4: Testing duplicate detection ---")

        # Extract existing links from the physics_papers.md file we created
        existing_links = extract_existing_arxiv_links(output_path1)
        print(f"Existing links: {existing_links}")

        # Create mock paper objects for testing
        class MockPaper:
            def __init__(self, title, entry_id):
                self.title = title
                self.entry_id = entry_id

        # Create test papers - one duplicate, one new
        test_papers = [
            MockPaper(
                "Dark Matter Detection with XENON", "http://arxiv.org/abs/2024.12345"
            ),  # Duplicate
            MockPaper(
                "New Gravitational Wave Detection", "http://arxiv.org/abs/2024.99999"
            ),  # New
        ]

        # Filter out duplicates
        filtered_papers = filter_new_papers(test_papers, existing_links)
        print(f"Original papers: {len(test_papers)}")
        print(f"Filtered papers: {len(filtered_papers)}")

        # Should filter out the duplicate
        assert len(filtered_papers) == 1, (
            f"Expected 1 paper after filtering, got {len(filtered_papers)}"
        )
        assert filtered_papers[0].entry_id == "http://arxiv.org/abs/2024.99999", (
            "Wrong paper remained after filtering"
        )

        print("✓ Duplicate detection working correctly")

        # Scenario 5: Testing with no duplicates
        print("\n--- Scenario 5: Testing with no duplicates ---")

        all_new_papers = [
            MockPaper(
                "Quantum Computing Breakthrough", "http://arxiv.org/abs/2024.11111"
            ),
            MockPaper(
                "Novel Superconductor Discovery", "http://arxiv.org/abs/2024.22222"
            ),
        ]

        filtered_all_new = filter_new_papers(all_new_papers, existing_links)
        assert len(filtered_all_new) == len(all_new_papers), (
            "All new papers should remain"
        )

        print("✓ All new papers correctly preserved")

        print("\n=== All scenarios tested successfully! ===")


if __name__ == "__main__":
    test_complete_append_workflow()
