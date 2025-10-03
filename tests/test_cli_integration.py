"""
Test that the main entry points can be imported and called without errors.
This ensures that the basic CLI functionality works.
"""

import pytest
from unittest.mock import patch
import tempfile
import os


def test_ciphr_hybrid_import():
    """Test that ciphr_hybrid can be imported successfully."""
    from ciphr import ciphr_hybrid

    assert hasattr(ciphr_hybrid, "main")


@patch("sys.argv", ["ciphr-hybrid", "--help"])
def test_ciphr_hybrid_help():
    """Test that ciphr-hybrid --help doesn't crash."""
    from ciphr.ciphr_hybrid import main

    with pytest.raises(SystemExit) as exc_info:
        main()

    # Help should exit with code 0
    assert exc_info.value.code == 0


def test_hybrid_workflow_data_collection_args():
    """Test that hybrid workflow accepts correct data collection arguments."""
    from ciphr.ciphr_hybrid import main

    with tempfile.TemporaryDirectory() as temp_dir:
        test_args = [
            "ciphr-hybrid",
            "--mode",
            "collect",
            "--tags",
            "hep-ex",
            "--max_results",
            "1",
            "--output_dir",
            temp_dir,
            "--verbose",
        ]

        with patch("sys.argv", test_args):
            with patch("ciphr.src.data_processor.search_arxiv", return_value=[]):
                # Should not crash with valid arguments
                try:
                    main()
                except SystemExit:
                    # May exit normally after processing
                    pass


def test_hybrid_workflow_process_args():
    """Test that hybrid workflow accepts correct process arguments."""
    from ciphr.ciphr_hybrid import main

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock files
        papers_file = os.path.join(temp_dir, "papers_data.json")
        llm_results_file = os.path.join(temp_dir, "llm_results.txt")

        with open(papers_file, "w") as f:
            f.write("[]")  # Empty papers array

        with open(llm_results_file, "w") as f:
            f.write("")  # Empty results

        test_args = [
            "ciphr-hybrid",
            "--mode",
            "process",
            "--output_dir",
            temp_dir,
            "--llm_results_file",
            llm_results_file,
            "--verbose",
        ]

        with patch("sys.argv", test_args):
            # Should not crash with valid arguments
            try:
                main()
            except SystemExit:
                # May exit normally after processing
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
