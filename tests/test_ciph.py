
import os
import shutil
import unittest
from unittest.mock import patch, MagicMock

from src.main import main
from config.config import LLM_QUESTIONS

class TestCIPhR(unittest.TestCase):

    def setUp(self):
        self.test_output_dir = "test_output"
        os.makedirs(self.test_output_dir, exist_ok=True)
        # Mock API keys for testing
        os.environ["FIRECRAWL_API_KEY"] = "dummy_firecrawl_key"
        os.environ["GEMINI_API_KEY"] = "dummy_gemini_key"

    def tearDown(self):
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
        del os.environ["FIRECRAWL_API_KEY"]
        del os.environ["GEMINI_API_KEY"]

    @patch("src.main.search_arxiv")
    @patch("src.main.download_pdf")
    @patch("src.main.get_abstract_content") # Corrected patch path
    @patch("src.llm_analyzer.LLMAnalyzer.extract_text_from_pdf")
    @patch("src.llm_analyzer.LLMAnalyzer.analyze_paper_with_llm")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_workflow(self, mock_parse_args, mock_analyze_paper, mock_extract_text, mock_get_abstract_content, mock_download_pdf, mock_search_arxiv):
        # Configure mock_parse_args to return a Namespace with expected arguments
        mock_parse_args.return_value = MagicMock(
            tags="hep-ph",
            max_results=1,
            output_dir=self.test_output_dir,
            output_filename="research_insights.md"
        )

        # Mock arXiv search results
        mock_paper = MagicMock()
        mock_paper.title = "Test Paper Title"
        mock_paper.entry_id = "http://arxiv.org/abs/2301.00001v1"
        mock_search_arxiv.return_value = [mock_paper]

        # Mock abstract content retrieval
        mock_get_abstract_content.return_value = "This is the abstract content."

        # Mock PDF download and text extraction
        mock_download_pdf.return_value = os.path.join(self.test_output_dir, "2301.00001v1.pdf")
        mock_extract_text.return_value = "This is the PDF content."

        # Mock LLM analysis
        mock_analyze_paper.return_value = {
            LLM_QUESTIONS[0]: "Experiment ran from 2020 to 2022.",
            LLM_QUESTIONS[1]: "Dark matter searches.",
            LLM_QUESTIONS[2]: "Calorimeter."
        }

        # Run the main function
        main()

        # Assertions
        mock_parse_args.assert_called_once() # Ensure parse_args was called
        mock_search_arxiv.assert_called_once() # This should now be called
        mock_get_abstract_content.assert_called_once_with(mock_paper) # Assert with mock_paper
        mock_download_pdf.assert_called_once()
        mock_extract_text.assert_called_once()
        mock_analyze_paper.assert_called_once()

        # Check if the output file was created and contains expected content
        output_file = os.path.join(self.test_output_dir, "research_insights.md")
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r") as f:
            content = f.read()
            self.assertIn("Test Paper Title", content)
            self.assertIn("[Link](http://arxiv.org/abs/2301.00001v1)", content)
            self.assertIn("Experiment ran from 2020 to 2022.", content)
            self.assertIn("Dark matter searches.", content)
            self.assertIn("Calorimeter.", content)

if __name__ == "__main__":
    unittest.main()


