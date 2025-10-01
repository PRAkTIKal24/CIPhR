import json
import logging
import os
from datetime import datetime
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ResultProcessor:
    """Handles processing of LLM analysis results and markdown generation."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def load_papers_data(self, filepath: str) -> List[Dict]:
        """Load papers data from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_llm_results(
        self, llm_output: str, questions: List[str]
    ) -> Dict[str, str]:
        """Parse LLM output and extract answers to questions."""
        answers = {}

        # Try to parse as JSON first (expected from run-gemini-cli)
        try:
            # Clean the output - remove any surrounding text
            import re

            # Look for JSON object in the output
            json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_answers = json.loads(json_str)

                # Map questions to answers with better matching
                for question in questions:
                    answer = None

                    # Try exact match first
                    if question in parsed_answers:
                        answer = parsed_answers[question]
                    else:
                        # Try partial matching with various strategies
                        question_lower = question.lower().strip()

                        for key, value in parsed_answers.items():
                            key_lower = key.lower().strip()

                            # Exact match (case insensitive)
                            if question_lower == key_lower:
                                answer = value
                                break

                            # Key contains question words
                            question_words = question_lower.split()[:3]  # First 3 words
                            if all(word in key_lower for word in question_words):
                                answer = value
                                break

                            # Question contains key words
                            key_words = key_lower.split()[:3]  # First 3 words
                            if all(word in question_lower for word in key_words):
                                answer = value
                                break

                    answers[question] = str(answer).strip() if answer else "Not found"

                return answers

        except (json.JSONDecodeError, AttributeError) as e:
            logging.warning(f"Could not parse LLM output as JSON: {e}")

        # Fallback: try to extract answers using text patterns
        logging.info("Falling back to text-based parsing")

        # Split by common separators
        sections = re.split(r"\n\s*\n|\n-|\n\d+\.", llm_output)

        for question in questions:
            answer = "Not found"
            question_keywords = question.lower().split()[:4]  # First 4 words

            for section in sections:
                section_lower = section.lower().strip()

                # Check if this section relates to the question
                if any(keyword in section_lower for keyword in question_keywords):
                    # Extract the answer part
                    lines = section.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        # Skip lines that are just the question
                        if len(line) > len(
                            question
                        ) + 5 and not line.lower().startswith(question.lower()[:10]):
                            # Clean up the answer
                            line = re.sub(
                                r"^[\d\.\-\*\s]*", "", line
                            )  # Remove leading numbers/bullets
                            line = re.sub(
                                r"^(answer|a):\s*", "", line, flags=re.IGNORECASE
                            )  # Remove "Answer:"
                            if line:
                                answer = line
                                break
                    break

            answers[question] = answer

        return answers

    def combine_results(
        self, papers_data: List[Dict], llm_results: List[str], questions: List[str]
    ) -> List[Dict]:
        """Combine paper data with LLM analysis results."""
        combined_results = []

        # Check if we have a single comprehensive LLM result that covers all papers
        if len(llm_results) == 1 and len(papers_data) > 1:
            logging.info(
                "Attempting to parse single comprehensive LLM result for multiple papers"
            )
            comprehensive_result = self.parse_comprehensive_llm_result(
                llm_results[0], papers_data, questions
            )
            if comprehensive_result:
                return comprehensive_result

        # Process individual results
        for i, (paper_data, llm_output) in enumerate(
            zip(papers_data, llm_results, strict=False)
        ):
            if not llm_output.strip():
                logging.warning(
                    f"Empty LLM output for paper {i + 1}: {paper_data['title']}"
                )
                llm_answers = {q: "Error or not found." for q in questions}
            else:
                try:
                    llm_answers = self.parse_llm_results(llm_output, questions)
                    # Check if all answers are empty or "Not found"
                    if all(
                        answer in ["Not found", "Error or not found.", ""]
                        for answer in llm_answers.values()
                    ):
                        logging.warning(
                            f"All LLM answers empty for paper {i + 1}, using fallback"
                        )
                        llm_answers = {
                            q: f"Error: Failed to parse LLM result for {paper_data['title'][:50]}..."
                            for q in questions
                        }
                except Exception as e:
                    logging.error(f"Error parsing LLM results for paper {i + 1}: {e}")
                    llm_answers = {
                        q: f"Error: Exception during parsing - {str(e)[:100]}"
                        for q in questions
                    }

            result = {
                "title": paper_data["title"],
                "arxiv_url": paper_data["arxiv_url"],
                "llm_answers": llm_answers,
                "metadata": {
                    "authors": paper_data.get("authors", []),
                    "published": paper_data.get("published"),
                    "categories": paper_data.get("categories", []),
                },
            }

            combined_results.append(result)

        return combined_results

    def parse_comprehensive_llm_result(
        self, llm_output: str, papers_data: List[Dict], questions: List[str]
    ) -> List[Dict]:
        """Parse a single LLM output that contains analysis for multiple papers."""
        try:
            import json
            import re

            # Look for JSON array in the output
            json_match = re.search(r"\[.*\]", llm_output, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)

                if isinstance(parsed_data, list) and len(parsed_data) == len(
                    papers_data
                ):
                    logging.info(
                        f"Successfully parsed comprehensive result for {len(parsed_data)} papers"
                    )

                    results = []
                    for _i, (paper_data, analysis) in enumerate(
                        zip(papers_data, parsed_data, strict=False)
                    ):
                        if isinstance(analysis, dict):
                            # Map the analysis results to our questions
                            llm_answers = {}
                            for question in questions:
                                answer = None

                                # Try exact match first
                                if question in analysis:
                                    answer = analysis[question]
                                else:
                                    # Try partial matching
                                    question_lower = question.lower().strip()
                                    for key, value in analysis.items():
                                        key_lower = key.lower().strip()
                                        if question_lower == key_lower or any(
                                            word in key_lower
                                            for word in question_lower.split()[:3]
                                        ):
                                            answer = value
                                            break

                                llm_answers[question] = (
                                    str(answer).strip() if answer else "Not found"
                                )
                        else:
                            # Fallback for non-dict analysis
                            llm_answers = {q: "Error parsing result" for q in questions}

                        result = {
                            "title": paper_data["title"],
                            "arxiv_url": paper_data["arxiv_url"],
                            "llm_answers": llm_answers,
                            "metadata": {
                                "authors": paper_data.get("authors", []),
                                "published": paper_data.get("published"),
                                "categories": paper_data.get("categories", []),
                            },
                        }
                        results.append(result)

                    return results

        except (json.JSONDecodeError, AttributeError) as e:
            logging.warning(f"Could not parse comprehensive LLM result: {e}")

        return None  # Fallback to individual processing

    def generate_markdown_table(
        self, results: List[Dict], questions: List[str], include_header: bool = True
    ) -> str:
        """Generate markdown table from analysis results."""
        if not results:
            return "No results to display."

        markdown = ""

        if include_header:
            # Prepare headers - using constants to avoid hardcoding
            TITLE_COLUMN = "Paper Title"
            LINK_COLUMN = "arXiv Link"
            headers = [TITLE_COLUMN, LINK_COLUMN] + [
                q.replace("\n", " ") for q in questions
            ]
            markdown += " | ".join(headers) + "\n"
            markdown += " | ".join(["-" * len(h) for h in headers]) + "\n"

        # Add rows
        for result in results:
            row = [result["title"], f"[Link]({result['arxiv_url']})"]
            for question in questions:
                answer = result["llm_answers"].get(question, "N/A")
                # Replace newlines in answers for single-line table cells
                row.append(answer.replace("\n", " "))
            markdown += " | ".join(row) + "\n"

        return markdown

    def extract_questions_from_existing_file(self, file_path: str) -> List[str]:
        """Extract LLM questions from existing markdown file by parsing the header row."""
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if len(lines) < 1:
                return []

            # Parse the header row (first line)
            header_line = lines[0].strip()
            headers = [h.strip() for h in header_line.split("|")]

            # Remove "Paper Title" and "arXiv Link" to get only LLM questions
            if len(headers) >= 2:
                llm_questions = headers[2:]  # Skip first two columns
                return [q for q in llm_questions if q]  # Remove empty strings

            return []
        except Exception as e:
            logging.warning(f"Error extracting questions from {file_path}: {e}")
            return []

    def questions_match(
        self, existing_questions: List[str], config_questions: List[str]
    ) -> bool:
        """Check if existing file questions exactly match config questions."""
        # Normalize questions by removing newlines and extra spaces
        existing_normalized = [q.replace("\n", " ").strip() for q in existing_questions]
        config_normalized = [q.replace("\n", " ").strip() for q in config_questions]

        return existing_normalized == config_normalized

    def generate_date_suffix(self) -> str:
        """Generate date suffix in ddmmyy format."""
        now = datetime.now()
        return now.strftime("%d%m%y")

    def get_output_filename(self, base_filename: str, questions: List[str]) -> str:
        """Determine the appropriate output filename based on existing file and question matching."""
        output_path = os.path.join(self.output_dir, base_filename)

        # Check if file exists
        if not os.path.exists(output_path):
            return base_filename

        # Extract questions from existing file
        existing_questions = self.extract_questions_from_existing_file(output_path)

        # Check if questions match
        if self.questions_match(existing_questions, questions):
            return base_filename  # Use original filename for appending

        # Create new filename with date suffix
        name, ext = os.path.splitext(base_filename)
        date_suffix = self.generate_date_suffix()
        return f"{name}_{date_suffix}{ext}"

    def save_results(
        self, results: List[Dict], questions: List[str], base_filename: str
    ) -> str:
        """Save results to markdown file with appropriate filename."""
        filename = self.get_output_filename(base_filename, questions)
        output_path = os.path.join(self.output_dir, filename)

        # Check if we should prepend to existing file
        should_prepend = filename == base_filename and os.path.exists(output_path)

        if should_prepend:
            # Prepend mode: add new results to the top of existing table
            # First read existing content
            with open(output_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            
            # Split existing content into header and data
            existing_lines = existing_content.strip().split('\n')
            if len(existing_lines) >= 2:
                header_line = existing_lines[0]
                separator_line = existing_lines[1]
                existing_data_lines = existing_lines[2:] if len(existing_lines) > 2 else []
                
                # Generate new data rows (without header)
                new_markdown_table = self.generate_markdown_table(
                    results, questions, include_header=False
                )
                new_data_lines = new_markdown_table.strip().split('\n') if new_markdown_table.strip() else []
                
                # Combine: header + separator + new data + existing data
                combined_lines = [header_line, separator_line] + new_data_lines + existing_data_lines
                combined_content = '\n'.join(combined_lines) + '\n'
                
                # Write the combined content
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(combined_content)
                
                logging.info(
                    f"Prepended {len(results)} new results to top of existing file: {output_path}"
                )
            else:
                # Existing file is malformed, treat as new file
                logging.warning(f"Existing file {output_path} appears malformed, creating new file")
                markdown_table = self.generate_markdown_table(
                    results, questions, include_header=True
                )
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_table)
                logging.info(f"Created new file (replacing malformed): {output_path}")
        else:
            # New file mode: include full table with header
            markdown_table = self.generate_markdown_table(
                results, questions, include_header=True
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_table)
            if filename != base_filename:
                logging.info(f"Created new file with date suffix: {output_path}")
            else:
                logging.info(f"Created new file: {output_path}")

        return output_path


if __name__ == "__main__":
    # Test the result processor
    processor = ResultProcessor()

    # Mock test data
    papers_data = [
        {
            "title": "Test Paper",
            "arxiv_url": "http://arxiv.org/abs/test",
            "abstract": "Test abstract",
        }
    ]

    llm_results = [
        '{"What is the main physics phenomenon": "Test phenomenon", "Is this related to dark matter": "No"}'
    ]

    questions = [
        "What is the main physics phenomenon",
        "Is this related to dark matter",
    ]

    combined = processor.combine_results(papers_data, llm_results, questions)
    markdown = processor.generate_markdown_table(combined, questions)
    print(markdown)
