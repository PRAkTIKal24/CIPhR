"""
Test script to verify the append functionality works correctly
without requiring real API keys.
"""

import os
import tempfile
from datetime import datetime

from ciphr.src.utils import (
    extract_existing_arxiv_links,
    filter_new_papers,
)
from ciphr.src.result_processor import ResultProcessor
from ciphr.config.config import LLM_QUESTIONS


def test_extract_questions():
    """Test extracting questions from existing markdown file."""
    processor = ResultProcessor()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file with questions
        test_file = os.path.join(temp_dir, "test_questions.md")
        test_content = """Paper Title | arXiv Link | Question 1 | Question 2 | Question 3
----------- | ---------- | ---------- | ---------- | ----------
Some Paper | [Link](http://arxiv.org/abs/test) | Answer 1 | Answer 2 | Answer 3
"""
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Test extracting questions from file
        questions = processor.extract_questions_from_existing_file(test_file)
        assert isinstance(questions, list)
        assert len(questions) == 3  # Should extract 3 questions
        assert questions == ["Question 1", "Question 2", "Question 3"]

        # Test on non-existent file
        no_questions = processor.extract_questions_from_existing_file(
            os.path.join(temp_dir, "nonexistent.md")
        )
        assert no_questions == []

        # Test with empty file
        empty_file = os.path.join(temp_dir, "empty.md")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("")

        empty_questions = processor.extract_questions_from_existing_file(empty_file)
        assert empty_questions == []


def test_questions_matching():
    """Test question matching logic."""
    processor = ResultProcessor()
    
    # Test identical questions
    identical = ["Question 1", "Question 2", "Question 3"]
    assert processor.questions_match(identical, identical)

    # Test different questions
    different = ["Question 1", "Question 2", "Different Question"]
    assert not processor.questions_match(different, identical)

    # Test with normalization (newlines and spaces)
    with_newlines = ["Question 1\n", "Question 2 ", " Question 3"]
    normalized = ["Question 1", "Question 2", "Question 3"]
    assert processor.questions_match(with_newlines, normalized)


def test_date_suffix():
    """Test date suffix generation."""
    processor = ResultProcessor()
    suffix = processor.generate_date_suffix()
    expected = datetime.now().strftime("%d%m%y")
    assert suffix == expected
    assert len(suffix) == 6  # ddmmyy format
    assert suffix.isdigit()


def test_filename_generation():
    """Test output filename generation logic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        processor = ResultProcessor(output_dir=temp_dir)
        
        # Test with non-existing file
        filename1 = processor.get_output_filename("nonexistent.md", LLM_QUESTIONS)
        assert filename1 == "nonexistent.md"

        # Create a test file with different questions than config
        test_file = os.path.join(temp_dir, "test_different_questions.md")
        different_content = """Paper Title | arXiv Link | Different Question 1 | Different Question 2
----------- | ---------- | -------------------- | --------------------
Some Paper | [Link](http://arxiv.org/abs/test) | Answer 1 | Answer 2
"""
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(different_content)

        # Test with existing file that has different questions
        filename2 = processor.get_output_filename("test_different_questions.md", LLM_QUESTIONS)
        # Should create new filename with date suffix since questions don't match
        assert filename2.startswith("test_different_questions_")
        assert filename2.endswith(".md")

        # Create a test file with matching questions
        test_file_matching = os.path.join(temp_dir, "test_matching_questions.md")
        matching_headers = ["Paper Title", "arXiv Link"] + [
            q.replace("\n", " ") for q in LLM_QUESTIONS
        ]
        matching_content = " | ".join(matching_headers) + "\n"
        matching_content += " | ".join(["-" * len(h) for h in matching_headers]) + "\n"
        matching_content += "Test Paper | [Link](http://arxiv.org/abs/test) | Answer 1 | Answer 2 | Answer 3\n"

        with open(test_file_matching, "w", encoding="utf-8") as f:
            f.write(matching_content)

        # Test with existing file that has matching questions
        filename3 = processor.get_output_filename("test_matching_questions.md", LLM_QUESTIONS)
        # Should use original filename since questions match
        assert filename3 == "test_matching_questions.md"


def test_markdown_generation():
    """Test markdown table generation."""
    processor = ResultProcessor()
    
    # Mock data for testing
    mock_results = [
        {
            "title": "Test Paper 1",
            "arxiv_url": "http://arxiv.org/abs/test1",
            "llm_answers": {
                "Question 1": "Answer 1",
                "Question 2": "Answer 2",
                "Question 3": "Answer 3",
            },
        }
    ]

    # Test with header
    markdown_with_header = processor.generate_markdown_table(
        mock_results, LLM_QUESTIONS, include_header=True
    )


def test_complete_workflow_logic():
    """Test the complete workflow logic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        processor = ResultProcessor(output_dir=temp_dir)
        
        # Test with non-existing file
        filename1 = processor.get_output_filename("nonexistent.md", LLM_QUESTIONS)
        file_path1 = os.path.join(temp_dir, filename1)
        should_append1 = filename1 == "nonexistent.md" and os.path.exists(file_path1)
        assert not should_append1  # File doesn't exist
        assert filename1 == "nonexistent.md"

        # Create a file with different questions
        different_file = os.path.join(temp_dir, "different_questions.md")
        different_content = """Paper Title | arXiv Link | Different Question 1 | Different Question 2
----------- | ---------- | -------------------- | --------------------
Some Paper | [Link](http://arxiv.org/abs/test) | Answer 1 | Answer 2
"""
        with open(different_file, "w", encoding="utf-8") as f:
            f.write(different_content)

        # Test logic for existing file with different questions
        filename2 = processor.get_output_filename("different_questions.md", LLM_QUESTIONS)
        file_path2 = os.path.join(temp_dir, filename2)
        should_append2 = filename2 == "different_questions.md" and os.path.exists(
            file_path2
        )

        # Since questions are different, should_append should be False
        assert not should_append2
        # The filename should have a date suffix
        assert filename2 != "different_questions.md"
        assert filename2.startswith("different_questions_")


def test_config_questions_structure():
    """Test that config questions are properly structured."""
    assert isinstance(LLM_QUESTIONS, list)
    assert len(LLM_QUESTIONS) > 0
    assert all(isinstance(q, str) for q in LLM_QUESTIONS)
    assert all(len(q.strip()) > 0 for q in LLM_QUESTIONS)


def test_extract_existing_arxiv_links():
    """Test extracting arXiv links from existing markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file with arXiv links
        test_file = os.path.join(temp_dir, "test_with_links.md")
        test_content = """Paper Title | arXiv Link | Question 1 | Question 2
----------- | ---------- | ---------- | ----------
Paper 1 | [Link](http://arxiv.org/abs/2024.12345) | Answer 1 | Answer 2
Paper 2 | [Link](http://arxiv.org/abs/2024.67890) | Answer 3 | Answer 4
Paper 3 | [Link](http://arxiv.org/abs/2024.11111) | Answer 5 | Answer 6
"""
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Test with file containing links
        links = extract_existing_arxiv_links(test_file)
        assert isinstance(links, set)
        assert len(links) == 3  # Should find 3 links in the test file

        # All links should be arXiv URLs
        expected_links = {
            "http://arxiv.org/abs/2024.12345",
            "http://arxiv.org/abs/2024.67890",
            "http://arxiv.org/abs/2024.11111",
        }
        assert links == expected_links

        # Test with non-existent file
        no_links = extract_existing_arxiv_links(
            os.path.join(temp_dir, "nonexistent.md")
        )
        assert no_links == set()

        # Test with file without links
        test_file_no_links = os.path.join(temp_dir, "no_links.md")
        no_links_content = """Paper Title | arXiv Link | Question 1
----------- | ---------- | ----------
Paper 1 | No Link | Answer 1
"""
        with open(test_file_no_links, "w", encoding="utf-8") as f:
            f.write(no_links_content)

        empty_links = extract_existing_arxiv_links(test_file_no_links)
        assert empty_links == set()


def test_filter_new_papers():
    """Test filtering papers based on existing links."""

    # Create mock paper objects
    class MockPaper:
        def __init__(self, title, entry_id):
            self.title = title
            self.entry_id = entry_id

    # Create test papers
    papers = [
        MockPaper("Paper 1", "http://arxiv.org/abs/2024.12345"),
        MockPaper("Paper 2", "http://arxiv.org/abs/2024.67890"),
        MockPaper("Paper 3", "http://arxiv.org/abs/2024.11111"),
    ]

    # Test with no existing links
    existing_links = set()
    filtered = filter_new_papers(papers, existing_links)
    assert len(filtered) == len(papers)  # All papers should be included

    # Test with some existing links
    existing_links = {
        "http://arxiv.org/abs/2024.12345",
        "http://arxiv.org/abs/2024.67890",
    }
    filtered = filter_new_papers(papers, existing_links)
    assert len(filtered) == 1  # Only one paper should remain
    assert filtered[0].entry_id == "http://arxiv.org/abs/2024.11111"

    # Test with all existing links
    existing_links = {paper.entry_id for paper in papers}
    filtered = filter_new_papers(papers, existing_links)
    assert len(filtered) == 0  # No papers should remain


def test_duplicate_detection_integration():
    """Test the complete duplicate detection workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file with existing links
        test_file = os.path.join(temp_dir, "existing_papers.md")
        test_content = """Paper Title | arXiv Link | Question 1
----------- | ---------- | ----------
Existing Paper 1 | [Link](http://arxiv.org/abs/2024.12345) | Answer 1
Existing Paper 2 | [Link](http://arxiv.org/abs/2024.67890) | Answer 2
"""
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Extract existing links
        existing_links = extract_existing_arxiv_links(test_file)
        assert len(existing_links) == 2

        # Create mock papers with some duplicates
        class MockPaper:
            def __init__(self, title, entry_id):
                self.title = title
                self.entry_id = entry_id

        # Create test papers - some duplicating existing links, some new
        test_papers = [
            MockPaper("New Paper", "http://arxiv.org/abs/2024.99999"),  # New
            MockPaper(
                "Existing Paper 1", "http://arxiv.org/abs/2024.12345"
            ),  # Duplicate
            MockPaper("Another New Paper", "http://arxiv.org/abs/2024.88888"),  # New
        ]

        # Filter papers
        filtered = filter_new_papers(test_papers, existing_links)

        # Should filter out existing papers
        assert len(filtered) == 2  # Only the new papers
        filtered_links = {paper.entry_id for paper in filtered}
        expected_new_links = {
            "http://arxiv.org/abs/2024.99999",
            "http://arxiv.org/abs/2024.88888",
        }
        assert filtered_links == expected_new_links
