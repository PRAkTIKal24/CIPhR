"""
Test script to verify the append functionality works correctly
without requiring real API keys.
"""
import os
import pytest
from datetime import datetime

from ciphr.ciphr import (
    extract_questions_from_existing_file,
    questions_match,
    generate_date_suffix,
    get_output_filename,
    generate_markdown_table
)
from ciphr.config.config import LLM_QUESTIONS


def test_extract_questions():
    """Test extracting questions from existing markdown file."""
    # Test on existing hepex.md
    existing_questions = extract_questions_from_existing_file('/workspaces/CIPhR/output/hepex.md')
    assert isinstance(existing_questions, list)
    
    # Test on newly created file
    new_questions = extract_questions_from_existing_file('/workspaces/CIPhR/output/hepex_250925.md')
    assert isinstance(new_questions, list)
    
    # Test on non-existent file
    no_questions = extract_questions_from_existing_file('/workspaces/CIPhR/output/nonexistent.md')
    assert no_questions == []


def test_questions_matching():
    """Test question matching logic."""
    # Test identical questions
    identical = ["Question 1", "Question 2", "Question 3"]
    assert questions_match(identical, identical) == True
    
    # Test different questions
    different = ["Question 1", "Question 2", "Different Question"]
    assert questions_match(different, identical) == False
    
    # Test with normalization (newlines and spaces)
    with_newlines = ["Question 1\n", "Question 2 ", " Question 3"]
    normalized = ["Question 1", "Question 2", "Question 3"]
    assert questions_match(with_newlines, normalized) == True


def test_date_suffix():
    """Test date suffix generation."""
    suffix = generate_date_suffix()
    expected = datetime.now().strftime("%d%m%y")
    assert suffix == expected
    assert len(suffix) == 6  # ddmmyy format
    assert suffix.isdigit()


def test_filename_generation():
    """Test output filename generation logic."""
    test_output_dir = '/workspaces/CIPhR/output'
    
    # Test with existing file that has different questions
    filename1 = get_output_filename('hepex.md', test_output_dir)
    # Should create new filename with date suffix since questions don't match
    assert filename1.startswith('hepex_')
    assert filename1.endswith('.md')
    
    # Test with non-existing file
    filename2 = get_output_filename('nonexistent.md', test_output_dir)
    assert filename2 == 'nonexistent.md'


def test_markdown_generation():
    """Test markdown table generation with and without headers."""
    # Create mock results
    mock_results = [
        {
            "title": "Test Paper 1",
            "arxiv_url": "http://arxiv.org/abs/test1",
            "llm_answers": {
                LLM_QUESTIONS[0]: "Physics phenomenon 1",
                LLM_QUESTIONS[1]: "Dark matter related",
                LLM_QUESTIONS[2]: "Yes, ATLAS detector"
            }
        }
    ]
    
    # Test with header
    markdown_with_header = generate_markdown_table(mock_results, include_header=True)
    assert "Paper Title" in markdown_with_header
    assert "arXiv Link" in markdown_with_header
    assert "---" in markdown_with_header  # Header separator
    assert "Test Paper 1" in markdown_with_header
    
    # Test without header (for appending)
    markdown_without_header = generate_markdown_table(mock_results, include_header=False)
    assert "Paper Title" not in markdown_without_header
    assert "---" not in markdown_without_header
    assert "Test Paper 1" in markdown_without_header
    
    # Test empty results
    empty_markdown = generate_markdown_table([])
    assert empty_markdown == "No results to display."


def test_complete_workflow_logic():
    """Test the complete workflow logic."""
    test_output_dir = '/workspaces/CIPhR/output'
    
    # Test logic for existing file with different questions
    filename = get_output_filename('hepex.md', test_output_dir)
    file_path = os.path.join(test_output_dir, filename)
    should_append = filename == 'hepex.md' and os.path.exists(file_path)
    
    # Since hepex.md has different questions, should_append should be False
    assert should_append == False
    
    # The filename should have a date suffix
    assert filename != 'hepex.md'
    assert filename.startswith('hepex_')


def test_config_questions_structure():
    """Test that config questions are properly structured."""
    assert isinstance(LLM_QUESTIONS, list)
    assert len(LLM_QUESTIONS) > 0
    assert all(isinstance(q, str) for q in LLM_QUESTIONS)
    assert all(len(q.strip()) > 0 for q in LLM_QUESTIONS)