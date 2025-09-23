
# CIPhR: Crawl and Ingest Physics Research

CIPhR is an automated tool designed to scrape particle physics research papers from arXiv, extract specific information using Large Language Model (LLM) analysis, and generate a living markdown table with research insights. This tool is built with Python, managed by `uv`, and designed for easy deployment with GitHub Actions.

## Features

- **arXiv Scraping**: Search and download physics papers from arXiv based on specified tags (e.g., `hep-ph`).
- **Firecrawl Integration**: Utilizes Firecrawl to scrape abstract pages for additional context.
- **LLM Analysis**: Employs Google Gemini 1.5 Flash to answer user-defined questions about the paper content.
- **Markdown Table Output**: Generates a concise markdown table summarizing the extracted information, including a citation to the paper link.
- **GitHub Actions Ready**: Configured for daily automated execution via GitHub Actions.
- **Temporary Storage**: Downloads PDFs to temporary storage and deletes them after processing to manage disk space.

## Project Structure

```
CIPhR/
├── .github/
│   └── workflows/
│       └── main.yml         # GitHub Actions workflow for daily runs
├── config/
│   └── config.py            # Configuration for API keys, arXiv tags, and LLM questions
├── data/                    # Directory for temporary PDF downloads (cleaned after processing)
├── src/
│   ├── __init__.py
│   ├── arxiv_scraper.py     # Handles arXiv searching, PDF downloading, and Firecrawl scraping
│   ├── llm_analyzer.py      # Manages PDF text extraction and LLM-based content analysis
│   └── main.py              # Main CLI script to orchestrate the workflow
├── .env                     # Environment variables for API keys (local development)
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── test_ciph.py             # Unit tests for the project
└── todo.md                  # Task list for development (internal)
```

## Setup and Installation

1.  **Clone the repository (or integrate into your existing TARP repo)**:

    ```bash
    git clone <your-tarp-repo-url>
    cd <your-tarp-repo-name>
    # If integrating, copy the CIPhR directory into your repo
    ```

2.  **Navigate to the CIPhR directory**:

    ```bash
    cd CIPhR
    ```

3.  **Install `uv` (if not already installed)**:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ```

4.  **Create a virtual environment and install dependencies**:

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    uv sync
    ```

5.  **Configure API Keys**: Create a `.env` file in the `CIPhR/` directory with your API keys:

    ```dotenv
    FIRECRAWL_API_KEY=your_firecrawl_api_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

    *Replace `your_firecrawl_api_key` and `your_gemini_api_key` with your actual keys.*

## Usage

Run the CIPhR tool from the command line:

```bash
    uv run ciphr \
    --tags hep-ex \
    --max_results 10 \
    --output_dir output \
    --output_filename hepex.md
```

### Command-line Arguments

-   `--tags`: Comma-separated arXiv categories/tags to search for (e.g., `hep-ph,nucl-ex`). Default is `hep-ph`.
-   `--max_results`: Maximum number of arXiv papers to process. Default is `5`.
-   `--output_dir`: Directory to save downloaded PDFs (temporarily) and the final markdown table. Default is `output`.
-   `--output_filename`: Filename for the markdown output table. Default is `research_insights.md`.

## Configuration

The `config/config.py` file allows you to customize default settings:

-   `FIRECRAWL_API_KEY`: Your Firecrawl API key (loaded from `.env`).
-   `GEMINI_API_KEY`: Your Gemini API key (loaded from `.env`).
-   `LLM_QUESTIONS`: A list of strings, where each string is a question you want the LLM to answer for each paper. Modify this list to tailor the extracted information.
-   `ARXIV_TAGS`: Default arXiv tags.
-   `MAX_ARXIV_RESULTS`: Default maximum number of results.

## GitHub Actions Automation

The `.github/workflows/main.yml` file sets up a daily GitHub Actions workflow:

-   It runs every day at 00:00 UTC.
-   It checks out the repository, sets up Python, installs `uv` and dependencies.
-   It runs the `src/main.py` script.
-   It uploads the generated `research_insights.md` as a workflow artifact.
-   It attempts to commit and push the updated `research_insights.md` back to the repository. **Note**: For this step to work, you might need to configure a `GITHUB_TOKEN` with write permissions or use a Personal Access Token (PAT) if the repository is protected. For public repositories, the default `GITHUB_TOKEN` usually has sufficient permissions for `pull_request` or `push` events.

### Setting up API Keys in GitHub Secrets

For the GitHub Actions workflow to access your API keys, you must add them as repository secrets:

1.  Go to your GitHub repository.
2.  Navigate to `Settings` > `Secrets and variables` > `Actions`.
3.  Click `New repository secret`.
4.  Add `FIRECRAWL_API_KEY` with your Firecrawl API key as its value.
5.  Add `GEMINI_API_KEY` with your Gemini API key as its value.

## Extending and Customizing

-   **New LLM Questions**: Simply update the `LLM_QUESTIONS` list in `config/config.py`.
-   **Different arXiv Categories**: Modify the `--tags` argument when running the script or the `ARXIV_TAGS` in `config/config.py`.
-   **Output Format**: The `generate_markdown_table` function in `src/main.py` can be modified to change the output format.

## License

This project is licensed under the MIT License.
