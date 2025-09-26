#!/usr/bin/env python3
"""
Test the improved LLM result parsing
"""
import json
import tempfile
import os
from ciphr.src.result_processor import ResultProcessor

def test_improved_parsing():
    """Test parsing of comprehensive LLM results."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Testing improved LLM result parsing...")
        
        # Mock papers data
        papers_data = [
            {"title": "Paper 1", "arxiv_url": "http://arxiv.org/abs/1", "authors": []},
            {"title": "Paper 2", "arxiv_url": "http://arxiv.org/abs/2", "authors": []},
            {"title": "Paper 3", "arxiv_url": "http://arxiv.org/abs/3", "authors": []}
        ]
        
        # Mock comprehensive LLM result (single response for all papers)
        comprehensive_result = [
            {
                "What is the main physics phenomenon studied by this paper": "Dark matter detection",
                "Is this work related to dark matter searches? If yes, how?": "Yes, direct detection",
                "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?": "Yes, XENON"
            },
            {
                "What is the main physics phenomenon studied by this paper": "Higgs physics",  
                "Is this work related to dark matter searches? If yes, how?": "No, Standard Model",
                "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?": "Yes, CMS"
            },
            {
                "What is the main physics phenomenon studied by this paper": "Neutrino oscillations",
                "Is this work related to dark matter searches? If yes, how?": "No, neutrino physics", 
                "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?": "Yes, T2K"
            }
        ]
        
        # Simulate what run-gemini-cli might return
        llm_output = f"Here are the analysis results:\n\n{json.dumps(comprehensive_result, indent=2)}\n\nAnalysis complete."
        
        # Test with single comprehensive result
        processor = ResultProcessor(temp_dir)
        questions = [
            "What is the main physics phenomenon studied by this paper",
            "Is this work related to dark matter searches? If yes, how?",
            "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?"
        ]
        
        # Test the comprehensive parser directly
        result = processor.parse_comprehensive_llm_result(llm_output, papers_data, questions)
        
        if result:
            print(f"✅ Comprehensive parsing successful! Got {len(result)} results")
            for i, res in enumerate(result):
                print(f"  Paper {i+1}: {res['title']}")
                print(f"    Phenomenon: {res['llm_answers'][questions[0]]}")
        else:
            print("❌ Comprehensive parsing failed")
        
        # Test the combine_results method with single comprehensive result
        llm_results = [llm_output]  # Single result for multiple papers
        combined = processor.combine_results(papers_data, llm_results, questions)
        
        print(f"\n✅ Combined results: {len(combined)} papers processed")
        
        # Verify results
        assert len(combined) == 3, f"Expected 3 results, got {len(combined)}"
        assert "Dark matter" in combined[0]['llm_answers'][questions[0]]
        assert "Higgs" in combined[1]['llm_answers'][questions[0]]  
        assert "Neutrino" in combined[2]['llm_answers'][questions[0]]
        
        print("✅ All parsing tests passed!")

if __name__ == "__main__":
    test_improved_parsing()