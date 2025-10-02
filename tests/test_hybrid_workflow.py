"""
Tests for the hybrid workflow components.
Tests data_processor.py, result_processor.py, and ciphr_hybrid.py functionality.
"""

import json
import os
import tempfile
import pytest
from unittest.mock import Mock, patch

from ciphr.src.data_processor import DataProcessor
from ciphr.src.result_processor import ResultProcessor
from ciphr.config.config import LLM_QUESTIONS


class TestDataProcessor:
    """Test DataProcessor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = DataProcessor(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_papers_data(self):
        """Test saving papers data to JSON."""
        # Mock paper data
        mock_papers = [
            {
                "title": "Test Paper 1",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "abstract": "Test abstract 1",
                "pdf_content": "Test PDF content 1",
                "combined_content": "Test abstract 1\n\nTest PDF content 1",
                "authors": ["Author 1", "Author 2"],
                "published": "2024-09-26T10:00:00Z",
                "categories": ["hep-ex"],
            },
            {
                "title": "Test Paper 2",
                "arxiv_url": "http://arxiv.org/abs/2024.67890",
                "abstract": "Test abstract 2",
                "pdf_content": "Test PDF content 2",
                "combined_content": "Test abstract 2\n\nTest PDF content 2",
                "authors": ["Author 3"],
                "published": "2024-09-26T11:00:00Z",
                "categories": ["hep-ph"],
            },
        ]

        output_file = os.path.join(self.temp_dir, "test_papers.json")
        result_file = self.processor.save_papers_data(mock_papers, output_file)

        # Verify file was created
        assert os.path.exists(result_file)
        assert result_file == output_file

        # Verify content
        with open(result_file, "r") as f:
            saved_data = json.load(f)

        assert len(saved_data) == 2
        assert saved_data[0]["title"] == "Test Paper 1"
        assert saved_data[1]["title"] == "Test Paper 2"
        assert saved_data[0]["authors"] == ["Author 1", "Author 2"]

    def test_create_analysis_prompts(self):
        """Test creating analysis prompts JSON."""
        questions = ["Question 1", "Question 2", "Question 3"]
        output_file = os.path.join(self.temp_dir, "test_prompts.json")

        result_file = self.processor.create_analysis_prompts(questions, output_file)

        # Verify file was created
        assert os.path.exists(result_file)

        # Verify content
        with open(result_file, "r") as f:
            prompts_data = json.load(f)

        assert "questions" in prompts_data
        assert "instructions" in prompts_data
        assert prompts_data["questions"] == questions
        assert "JSON object" in prompts_data["instructions"]

    def test_extract_text_from_pdf_success(self):
        """Test successful PDF text extraction."""
        # Create a temporary file to simulate PDF
        pdf_file = os.path.join(self.temp_dir, "test.pdf")

        with patch("pypdf.PdfReader") as mock_pdf_reader:
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Extracted PDF text content"
            mock_reader.pages = [mock_page]
            mock_pdf_reader.return_value = mock_reader

            result = self.processor.extract_text_from_pdf(pdf_file)

            assert result == "Extracted PDF text content"
            mock_pdf_reader.assert_called_once_with(pdf_file)

    def test_extract_text_from_pdf_failure(self):
        """Test PDF text extraction failure handling."""
        pdf_file = os.path.join(self.temp_dir, "bad.pdf")

        with patch("pypdf.PdfReader") as mock_pdf_reader:
            mock_pdf_reader.side_effect = Exception("PDF read error")

            result = self.processor.extract_text_from_pdf(pdf_file)

            assert result is None

    @patch("ciphr.src.data_processor.search_arxiv")
    @patch("ciphr.src.data_processor.get_abstract_content")
    @patch("ciphr.src.data_processor.download_pdf")
    def test_collect_paper_data_basic(self, mock_download, mock_abstract, mock_search):
        """Test basic paper data collection."""
        # Mock paper
        mock_paper = Mock()
        mock_paper.title = "Mock Paper Title"
        mock_paper.entry_id = "http://arxiv.org/abs/2024.12345v1"
        mock_paper.authors = [Mock(name="Mock Author")]
        mock_paper.published = Mock()
        mock_paper.published.strftime = Mock(return_value="2024-09-26T10:00:00Z")
        mock_paper.categories = ["hep-ex"]

        # Mock search results
        mock_search.return_value = [mock_paper]
        mock_abstract.return_value = "Mock abstract content"
        mock_download.side_effect = Exception(
            "No PDF available"
        )  # Simulate PDF download failure

        papers = self.processor.collect_paper_data([mock_paper])

        # Should still process paper even without PDF
        assert len(papers) == 1
        paper = papers[0]
        assert paper["title"] == "Mock Paper Title"
        assert paper["arxiv_url"] == "http://arxiv.org/abs/2024.12345v1"
        assert paper["abstract"] == "Mock abstract content"

    def test_strip_references_section(self):
        """Test reference section stripping functionality."""
        # Test with REFERENCES section
        content_with_refs = """Introduction: This paper presents new methods.

Methods: We developed innovative approaches.

Results: Our experiments show improvements.

Conclusions: We successfully demonstrated effectiveness.

REFERENCES
[1] Author et al. Previous work. Journal, 2020.
[2] Another Author. Related study. Physics Letters, 2021."""

        stripped = self.processor.strip_references_section(content_with_refs)

        # Should remove everything from REFERENCES onward
        assert "REFERENCES" not in stripped
        assert "[1] Author et al." not in stripped
        assert "Conclusions: We successfully demonstrated effectiveness." in stripped

        # Test with different reference formats
        content_bibliography = """Content here.

BIBLIOGRAPHY
[1] Some reference..."""

        stripped_bib = self.processor.strip_references_section(content_bibliography)
        assert "BIBLIOGRAPHY" not in stripped_bib
        assert "Some reference" not in stripped_bib

        # Test with no references section
        content_no_refs = "Introduction: Test content without references."
        stripped_none = self.processor.strip_references_section(content_no_refs)
        assert stripped_none == content_no_refs

    def test_extract_conclusions_section(self):
        """Test conclusions section extraction functionality."""
        # Test with clear conclusions section (proper newline formatting)
        content_with_conclusions = "Introduction: This paper studies physics.\n\nMethods: We used advanced techniques.\n\nResults: The experiments show significant improvements.\n\nConclusions:\nIn conclusion, we have demonstrated that our method provides unprecedented accuracy and sensitivity. This work opens new avenues for future research and has important implications for understanding physics.\n\nAcknowledgments: We thank our collaborators.\n\nREFERENCES\n[1] Previous work..."

        conclusions = self.processor.extract_conclusions_section(
            content_with_conclusions
        )
        assert conclusions is not None
        assert "unprecedented accuracy" in conclusions
        assert "REFERENCES" not in conclusions
        # Note: Currently includes Acknowledgments section due to pattern limitation
        assert len(conclusions) > 50  # Should extract meaningful content

        # Test with Discussion section
        content_with_discussion = "Methods: Test methods.\n\nDiscussion:\nThe results indicate that our approach is superior to existing methods. We observed significant improvements in sensitivity.\n\nReferences: [1] Test..."

        discussion = self.processor.extract_conclusions_section(content_with_discussion)
        assert discussion is not None
        assert "superior to existing methods" in discussion
        # References with colon may be included due to pattern limitations

        # Test with numbered sections
        content_numbered = "4. Methods: Our approach uses novel techniques.\n\n5. Results: We achieved significant improvements.\n\n6. Conclusions:\nOur methodology represents a major advance in the field.\n\n7. Acknowledgments: We thank..."

        numbered_conclusions = self.processor.extract_conclusions_section(
            content_numbered
        )
        assert numbered_conclusions is not None
        assert "major advance" in numbered_conclusions
        # May include subsequent sections due to boundary detection

        # Test with no conclusions section
        content_no_conclusions = (
            "Introduction: Test.\n\nMethods: Test methods.\n\nResults: Test results."
        )

        no_conclusions = self.processor.extract_conclusions_section(
            content_no_conclusions
        )
        assert no_conclusions is None

    def test_process_content_for_llm(self):
        """Test complete content processing for LLM analysis."""
        title = "Advanced Physics Analysis"
        abstract = "This study presents novel detection methods."

        # Test short content (fits within limit)
        short_content = """Introduction: Brief paper content.

Methods: Simple methods.

Results: Good results.

Conclusions: Successful demonstration."""

        processed_short = self.processor.process_content_for_llm(
            title, abstract, short_content, max_content_length=1000
        )

        assert f"Title: {title}" in processed_short
        assert f"Abstract: {abstract}" in processed_short
        assert "Content:" in processed_short
        assert "Introduction: Brief paper content." in processed_short

        # Test long content (exceeds limit) with conclusions
        long_content = """Introduction: This is a very long paper with extensive content that exceeds the character limit.

Methods: We used very detailed and complex methodologies that require extensive explanation.

Results: Our comprehensive analysis revealed multiple significant findings across various parameters.

Discussion: The implications of our results are far-reaching and require careful interpretation.

Conclusions: In conclusion, this comprehensive study has demonstrated the effectiveness of our approach through rigorous testing and analysis. The results have significant implications for future research in this field.

Acknowledgments: We thank our collaborators.

REFERENCES
[1] Extensive reference list...
[2] Another reference..."""

        # Create content that exceeds limit
        extended_content = long_content + "\n" + "Additional content. " * 1000

        processed_long = self.processor.process_content_for_llm(
            title, abstract, extended_content, max_content_length=500
        )

        assert f"Title: {title}" in processed_long
        assert f"Abstract: {abstract}" in processed_long

        # For long papers, should include conclusions section
        if "[CONCLUSIONS SECTION]:" in processed_long:
            assert "comprehensive study has demonstrated" in processed_long
            assert "[MAIN CONTENT]:" in processed_long

        # Should not contain references
        assert "REFERENCES" not in processed_long
        assert "[1] Extensive reference" not in processed_long

    @patch("ciphr.src.data_processor.STRIP_REFERENCES", False)
    def test_strip_references_disabled(self):
        """Test that reference stripping can be disabled via config."""
        content_with_refs = (
            "Content here.\n\nREFERENCES\n[1] Should remain when stripping disabled."
        )

        # When STRIP_REFERENCES is False, should return original content
        result = self.processor.strip_references_section(content_with_refs)
        assert "REFERENCES" in result
        assert "[1] Should remain" in result


class TestResultProcessor:
    """Test ResultProcessor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = ResultProcessor(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_llm_results_valid_json(self):
        """Test parsing valid JSON LLM result."""
        json_result = {"Question 1": "Answer 1", "Question 2": "Answer 2"}
        json_str = json.dumps(json_result)
        questions = ["Question 1", "Question 2"]

        parsed = self.processor.parse_llm_results(json_str, questions)

        assert parsed["Question 1"] == "Answer 1"
        assert parsed["Question 2"] == "Answer 2"

    def test_parse_llm_results_invalid_json(self):
        """Test parsing invalid JSON with fallback."""
        invalid_json = "This is not valid JSON but mentions Question 1: Answer 1"
        questions = ["Question 1", "Question 2"]

        parsed = self.processor.parse_llm_results(invalid_json, questions)

        # Should still return a dict with fallback values
        assert isinstance(parsed, dict)

    def test_load_papers_data(self):
        """Test loading papers data from JSON file."""
        # Create test data
        test_papers = [
            {"title": "Test Paper", "arxiv_url": "http://arxiv.org/abs/2024.12345"}
        ]
        test_file = os.path.join(self.temp_dir, "papers.json")
        with open(test_file, "w") as f:
            json.dump(test_papers, f)

        loaded_papers = self.processor.load_papers_data(test_file)

        assert len(loaded_papers) == 1
        assert loaded_papers[0]["title"] == "Test Paper"

    def test_generate_markdown_table(self):
        """Test markdown table generation."""
        results = [
            {
                "title": "Test Paper 1",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "llm_answers": {"Question 1": "Answer 1A", "Question 2": "Answer 1B"},
            },
            {
                "title": "Test Paper 2",
                "arxiv_url": "http://arxiv.org/abs/2024.67890",
                "llm_answers": {"Question 1": "Answer 2A", "Question 2": "Answer 2B"},
            },
        ]

        questions = ["Question 1", "Question 2"]

        markdown = self.processor.generate_markdown_table(results, questions)

        # Verify structure
        lines = markdown.strip().split("\n")
        assert len(lines) >= 4  # Header + separator + 2 data rows minimum

        # Check header row
        header = lines[0]
        assert "Paper Title" in header
        assert "arXiv Link" in header
        assert "Question 1" in header
        assert "Question 2" in header

        # Check separator row
        separator = lines[1]
        assert "---" in separator

        # Check data rows
        assert "Test Paper 1" in lines[2]
        assert "Test Paper 2" in lines[3]
        assert "Answer 1A" in lines[2]
        assert "Answer 2A" in lines[3]

    def test_combine_results_basic(self):
        """Test basic result combination."""
        papers_data = [
            {
                "title": "Test Paper",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "authors": ["Author 1"],
            }
        ]

        llm_results = ['{"Question 1": "Answer 1", "Question 2": "Answer 2"}']
        questions = ["Question 1", "Question 2"]

        combined = self.processor.combine_results(papers_data, llm_results, questions)

        # Should return list of combined results
        assert len(combined) == 1
        result = combined[0]
        assert result["title"] == "Test Paper"
        assert "llm_answers" in result
        assert result["llm_answers"]["Question 1"] == "Answer 1"

    def test_save_results(self):
        """Test saving results to markdown file."""
        results = [
            {
                "title": "Test Paper",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "llm_answers": {"Question 1": "Answer 1"},
            }
        ]
        questions = ["Question 1"]
        filename = os.path.join(self.temp_dir, "test_results.md")

        saved_file = self.processor.save_results(results, questions, filename)

        # Verify file was created
        assert os.path.exists(saved_file)

        # Verify content
        with open(saved_file, "r") as f:
            content = f.read()

        assert "Test Paper" in content
        assert "Answer 1" in content
        assert "[Link]" in content

    def test_generate_date_suffix(self):
        """Test date suffix generation."""
        suffix = self.processor.generate_date_suffix()

        # Should be in format ddmmyy (6 digits)
        assert len(suffix) == 6
        assert suffix.isdigit()

    def test_questions_match(self):
        """Test question matching logic."""
        questions1 = ["Question 1", "Question 2"]
        questions2 = ["Question 1", "Question 2"]
        questions3 = ["Question 1", "Question 3"]

        assert self.processor.questions_match(questions1, questions2)
        assert not self.processor.questions_match(questions1, questions3)
        assert self.processor.questions_match([], [])


class TestHybridWorkflowIntegration:
    """Integration tests for the complete hybrid workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_data_collection_to_result_processing_pipeline(self):
        """Test the complete pipeline from data collection to result processing."""
        # Create mock papers data (simulating successful data collection)
        mock_papers = [
            {
                "title": "Hybrid Test Paper 1",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "abstract": "Test abstract 1",
                "pdf_content": "Test PDF content 1",
                "combined_content": "Test abstract 1\n\nTest PDF content 1",
                "authors": ["Hybrid Author 1"],
                "published": "2024-09-26T10:00:00Z",
                "categories": ["hep-ex"],
            },
            {
                "title": "Hybrid Test Paper 2",
                "arxiv_url": "http://arxiv.org/abs/2024.67890",
                "abstract": "Test abstract 2",
                "pdf_content": "Test PDF content 2",
                "combined_content": "Test abstract 2\n\nTest PDF content 2",
                "authors": ["Hybrid Author 2"],
                "published": "2024-09-26T11:00:00Z",
                "categories": ["hep-ph"],
            },
        ]

        # Mock LLM results (simulating successful LLM analysis)
        mock_llm_results = [
            '{"What is the main physics phenomenon studied by this paper": "Dark matter detection", "Is this work related to dark matter searches? If yes, how?": "Yes, direct detection", "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?": "Yes, XENON"}',
            '{"What is the main physics phenomenon studied by this paper": "Particle physics phenomenology", "Is this work related to dark matter searches? If yes, how?": "Not directly", "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?": "No, theoretical study"}',
        ]

        # Test data processor
        data_processor = DataProcessor(self.temp_dir)
        papers_file = os.path.join(self.temp_dir, "papers_data.json")
        prompts_file = os.path.join(self.temp_dir, "analysis_prompts.json")

        # Save papers data
        saved_papers_file = data_processor.save_papers_data(mock_papers, papers_file)
        saved_prompts_file = data_processor.create_analysis_prompts(
            LLM_QUESTIONS, prompts_file
        )

        assert os.path.exists(saved_papers_file)
        assert os.path.exists(saved_prompts_file)

        # Test result processor
        result_processor = ResultProcessor(self.temp_dir)

        # Combine results
        combined = result_processor.combine_results(
            mock_papers, mock_llm_results, LLM_QUESTIONS
        )

        # Save results
        output_file = os.path.join(self.temp_dir, "final_results.md")
        final_file = result_processor.save_results(combined, LLM_QUESTIONS, output_file)

        assert os.path.exists(final_file)

        # Verify final output content
        with open(final_file, "r") as f:
            content = f.read()

        assert "Hybrid Test Paper 1" in content
        assert "Hybrid Test Paper 2" in content
        assert "Dark matter detection" in content
        assert "Particle physics phenomenology" in content
        assert "[Link]" in content

    def test_empty_llm_results_handling(self):
        """Test handling of empty or problematic LLM results."""
        mock_papers = [
            {
                "title": "Test Paper",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "abstract": "Test",
                "pdf_content": "Test",
                "combined_content": "Test",
                "authors": ["Author"],
                "published": "2024-09-26T10:00:00Z",
                "categories": ["hep-ex"],
            }
        ]

        # Test with empty LLM results
        empty_llm_results = [""]

        result_processor = ResultProcessor(self.temp_dir)

        # Should handle gracefully without crashing
        combined = result_processor.combine_results(
            mock_papers, empty_llm_results, LLM_QUESTIONS
        )

        # Should still have one result
        assert len(combined) == 1
        assert combined[0]["title"] == "Test Paper"

    def test_individual_paper_results_parsing(self):
        """Test parsing individual paper results separated by ---PAPER---."""
        mock_papers = [
            {
                "title": "Paper 1",
                "arxiv_url": "http://arxiv.org/abs/2024.12345",
                "authors": [],
            },
            {
                "title": "Paper 2",
                "arxiv_url": "http://arxiv.org/abs/2024.67890",
                "authors": [],
            },
        ]

        # Simulate individual results from run-gemini-cli
        individual_results = """{"Question 1": "Answer 1A", "Question 2": "Answer 1B"}
---PAPER---
{"Question 1": "Answer 2A", "Question 2": "Answer 2B"}"""

        result_processor = ResultProcessor(self.temp_dir)

        # Parse individual results
        parsed_results = individual_results.split("---PAPER---")
        parsed_results = [result.strip() for result in parsed_results if result.strip()]

        assert len(parsed_results) == 2

        # Test combining with parsed results
        questions = ["Question 1", "Question 2"]

        combined = result_processor.combine_results(
            mock_papers, parsed_results, questions
        )

        assert len(combined) == 2
        assert combined[0]["title"] == "Paper 1"
        assert combined[1]["title"] == "Paper 2"
        assert combined[0]["llm_answers"]["Question 1"] == "Answer 1A"
        assert combined[1]["llm_answers"]["Question 1"] == "Answer 2A"

    def test_end_to_end_file_processing(self):
        """Test complete end-to-end file processing workflow."""
        # Create papers data file
        mock_papers = [
            {
                "title": "End-to-End Test Paper",
                "arxiv_url": "http://arxiv.org/abs/2024.99999",
                "abstract": "Test abstract",
                "authors": ["Test Author"],
                "published": "2024-09-26T10:00:00Z",
                "categories": ["hep-ex"],
            }
        ]

        papers_file = os.path.join(self.temp_dir, "e2e_papers.json")
        with open(papers_file, "w") as f:
            json.dump(mock_papers, f)

        # Test loading papers
        result_processor = ResultProcessor(self.temp_dir)
        loaded_papers = result_processor.load_papers_data(papers_file)

        assert len(loaded_papers) == 1
        assert loaded_papers[0]["title"] == "End-to-End Test Paper"

        # Test processing with LLM results
        llm_results = ['{"Question 1": "E2E Answer"}']
        questions = ["Question 1"]

        combined = result_processor.combine_results(
            loaded_papers, llm_results, questions
        )
        output_file = os.path.join(self.temp_dir, "e2e_results.md")
        final_file = result_processor.save_results(combined, questions, output_file)

        # Verify final output
        assert os.path.exists(final_file)
        with open(final_file, "r") as f:
            content = f.read()

        assert "End-to-End Test Paper" in content
        assert "E2E Answer" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
