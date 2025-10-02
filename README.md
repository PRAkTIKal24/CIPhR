[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17244567.svg)](https://doi.org/10.5281/zenodo.17244567)
![GitHub Release-date](https://img.shields.io/github/release-date-pre/PRAkTIKal24/CIPhR?style=flat&color=blue)
![Release-version](https://img.shields.io/github/v/tag/PRAkTIKal24/CIPhR?include_prereleases&label=latest%20release&color=blue)
![GitHub repo size](https://img.shields.io/github/repo-size/PRAkTIKal24/CIPhR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![GitHub forks](https://img.shields.io/github/forks/PRAkTIKal24/CIPhR?style=flat&color=blue)

[![tests](https://github.com/PRAkTIKal24/CIPhR/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/PRAkTIKal24/CIPhR/actions)



# CIPhR: Crawl and Ingest Physics Research

> 🚀 **Status**: Production ready with hybrid workflow ✅  
> 🔧 **Latest**: Individual paper processing prevents empty LLM results  
> 📅 **Updated**: September 2025 - All authentication and workflow issues resolved

CIPhR is an automated tool designed to scrape particle physics research papers from arXiv, extract specific information using Large Language Model (LLM) analysis, and generate a living markdown table with research insights. This tool is built with Python, managed by `uv`, and designed for easy deployment with GitHub Actions that smartly append to output files without duplicating entries.

## Features

- **arXiv Scraping**: Search and download physics papers from arXiv based on specified tags (e.g., `hep-ph`).
- **Firecrawl Integration**: Utilizes Firecrawl to scrape abstract pages for additional context.
- **LLM Analysis**: Employs Google Gemini 1.5 Flash to answer user-defined questions about the paper content.
- **Markdown Table Output**: Generates a concise markdown table summarizing the extracted information, including a citation to the paper link.
- **GitHub Actions Ready**: Configured for daily automated execution via GitHub Actions.
- **Temporary Storage**: Downloads PDFs to temporary storage and deletes them after processing to manage disk space.
- **✅ Hybrid Workflow**: Robust production approach using `google-github-actions/run-gemini-cli` for reliable authentication and individual paper processing to prevent empty results.
- **Individual Paper Processing**: Processes each paper separately to ensure reliable LLM analysis results.
- **Duplicate Detection**: Automatically skips papers that have already been processed.
- **🤖 Mattermost Integration**: Automatically posts notifications to Mattermost channels when papers using machine learning for dark matter research are discovered.

## 🚀 Mattermost ML4DM Bot Integration

CIPhR now includes intelligent Mattermost integration that automatically detects papers using **Machine Learning for Dark Matter (ML4DM)** research and posts notifications to your Mattermost channels.

### Features

- **Smart Detection**: Analyzes papers with an additional ML4DM flag question: *"Does this paper use ML techniques for dark matter searches? And if yes, list the main ML techniques used in this paper"*
- **Conditional Posting**: Only posts to Mattermost when ML4DM papers are found (avoids spam)
- **Single Daily Summary**: Posts one consolidated message per workflow run, not per paper
- **Rich Formatting**: Beautiful messages with emojis, markdown tables, and links to full analysis
- **ML Technique Extraction**: Highlights specific machine learning methods used in each paper

### Example Mattermost Message

```
🚀 🤖 New ML4DM papers on arXiv today! Found 2 papers using ML techniques for dark matter searches.

| Paper Title | arXiv Link | ML Techniques |
|---|---|---|
| Machine Learning for Dark Matter Detection at the LHC | [Link](http://arxiv.org/abs/2310.12345) | convolutional neural networks, random forest classifiers, gradient boosting |
| Neural Networks for Dark Matter Direct Detection | [Link](http://arxiv.org/abs/2310.67890) | deep neural networks, support vector machines |

📊 [View full analysis table here](https://github.com/PRAkTIKal24/CIPhR/blob/main/output/hepex.md)
```

### Setup

1. **Get Mattermost Webhook URL**: Create an incoming webhook in your Mattermost channel settings
2. **Add to GitHub Secrets**: Add `MM_WEBHOOK_URL` as a repository secret with your webhook URL
3. **Automatic Operation**: The workflow automatically detects ML4DM papers and posts when found

### Technical Details

- **No Impact on Main Output**: The ML4DM question is only used for Mattermost detection, not included in the main research table
- **Robust Detection**: Uses advanced pattern matching to identify ML usage in LLM responses
- **Error Handling**: Gracefully handles webhook failures without affecting the main workflow
- **Efficient Processing**: Minimal overhead - only processes papers that pass the ML4DM filter

## Project Structure

```
CIPhR/
├── .github/
│   └── workflows/
│       └── main.yml              # GitHub Actions workflow (hybrid approach)
├── ciphr/
│   ├── config/
│   │   └── config.py             # Configuration for API keys, arXiv tags, and LLM questions
│   ├── src/
│   │   ├── arxiv_scraper.py      # Handles arXiv searching and PDF downloading
│   │   ├── llm_analyzer.py       # Original LLM analysis (legacy)
│   │   ├── data_processor.py     # 🆕 Data collection for hybrid workflow
│   │   ├── result_processor.py   # 🆕 Result processing for hybrid workflow
│   │   └── mattermost_notifier.py # 🤖 ML4DM detection and Mattermost posting
│   ├── ciphr.py                  # Original single-phase workflow
│   └── ciphr_hybrid.py           # 🆕 Hybrid workflow orchestrator
├── output/                       # Generated research insights and intermediate files
├── tests/                        # Unit tests for the project
├── pyproject.toml               # Python project configuration (uv-based)
├── README.md                    # This file
├── HYBRID_WORKFLOW.md           # 🆕 Detailed hybrid workflow guide
└── .env                         # Environment variables for API keys (local development)
```

## Setup and Installation

1.  **Clone the repository

    ```bash
    git clone git@github.com:PRAkTIKal24/CIPhR.git
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

    If you want to develop new features add install the `dev-dependencies` as well:

    ```bash
    uv pip install --group dev

    ```

5.  **Configure API Keys**: Open the `.env` file that should contain `API-KEY` fields:
    
    ```dotenv
    FIRECRAWL_API_KEY=your_firecrawl_api_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

    *Replace `your_firecrawl_api_key` and `your_gemini_api_key` with your actual keys.*

## Usage

### 🚀 Hybrid Workflow (Recommended for CI workflows)

For improved reliability and authentication in GitHub Actions, use the hybrid workflow:

**Data Collection:**
```bash
uv run ciphr-hybrid --mode collect --tags hep-ex --max_results 10 --output_dir output --output_filename hepex.md --verbose
```

**Result Processing (after LLM analysis):**
```bash
uv run ciphr-hybrid --mode process --output_dir output --output_filename hepex.md --verbose
```

**Local Full Workflow (requires API keys):**
```bash
uv run ciphr-hybrid --mode full --tags hep-ex --max_results 10 --output_dir output --output_filename hepex.md --verbose
```

> ⚠️ **Note**: The `--mode full` option requires local GEMINI_API_KEY for LLM analysis. For production use, use the GitHub Actions workflow which handles LLM analysis via the `run-gemini-cli` action. See [ciphr.yml](https://github.com/PRAkTIKal24/CIPhR/blob/main/.github/workflows/ciphr.yml) for a production workflow example.

> 📖 **For detailed hybrid workflow instructions, see [HYBRID_WORKFLOW.md](HYBRID_WORKFLOW.md)**

### 🔧 Local Workflow

The original single-command approach still works for local development:

```bash
uv run ciphr --tags hep-ex --max_results 10 --output_dir output --output_filename hepex.md
```

### Command-line Arguments

-   `--tags`: Comma-separated arXiv categories/tags to search for (e.g., `hep-ph,nucl-ex`). Default is `hep-ph`.
-   `--max_results`: Maximum number of arXiv papers to process. Default is `5`.
-   `--output_dir`: Directory to save downloaded PDFs (temporarily) and the final markdown table. Default is `output`.
-   `--output_filename`: Filename for the markdown output table. Default is `research_insights.md`.
-   `--mode`: Operating mode - `collect` (data only), `process` (results only), or `full` (complete workflow).
-   `--llm_results_file`: File containing LLM analysis results (for process mode). Default is `llm_results.txt`.
-   `--verbose`: Enable detailed logging for debugging.

## Configuration

The `config/config.py` file allows you to customize default settings:

-   `FIRECRAWL_API_KEY`: Your Firecrawl API key (loaded from `.env`).
-   `GEMINI_API_KEY`: Your Gemini API key (loaded from `.env`).
-   `LLM_QUESTIONS`: A list of strings, where each string is a question you want the LLM to answer for each paper. Modify this list to tailor the extracted information.
-   `ARXIV_TAGS`: Default arXiv tags.
-   `MAX_ARXIV_RESULTS`: Default maximum number of results.

## GitHub Actions Automation

### ✅ Hybrid Workflow (Production Ready)

The current `.github/workflows/ciphr.yml` uses the hybrid approach with three phases:

1. **Data Collection**: Scrapes arXiv and processes PDFs using `uv run ciphr-hybrid --mode collect`
2. **LLM Analysis**: Individual paper analysis using `google-github-actions/run-gemini-cli@v0` (analyze-1 through analyze-5 steps)
3. **Result Processing**: Combines individual results and generates final markdown tables using `uv run ciphr-hybrid --mode process`

**Benefits:**
- ✅ Solves authentication issues in GitHub Actions environments
- ✅ Individual paper processing prevents empty LLM results
- ✅ More reliable error handling and recovery
- ✅ Better logging and debugging capabilities
- ✅ Maintained by Google for long-term stability
- ✅ Results separated by `---PAPER---` delimiter for reliable parsing
- 🤖 Intelligent ML4DM detection and Mattermost notifications

**Schedule:** 
- Runs every day at 00:00 UTC
- Manual triggering available via workflow_dispatch

### 🔧 Legacy Workflow

The original single-phase workflow is still available but may experience authentication issues in GitHub Actions environments due to GCP environment auto-detection.

### Setting up API Keys and Webhooks in GitHub Secrets

For the GitHub Actions workflow to access your API keys and Mattermost webhook, you must add them as repository secrets:

1.  Go to your GitHub repository.
2.  Navigate to `Settings` > `Secrets and variables` > `Actions`.
3.  Click `New repository secret`.
4.  Add `GEMINI_API_KEY` with your [Google AI Studio API key](https://aistudio.google.com/app/apikey) as its value.
5.  Add `FIRECRAWL_API_KEY` with your Firecrawl API key as its value (optional, for enhanced scraping).
6.  🤖 Add `MM_WEBHOOK_URL` with your Mattermost incoming webhook URL (optional, for ML4DM notifications).

> 🔑 **Note**: The hybrid workflow only requires `GEMINI_API_KEY` for core functionality. The `google-github-actions/run-gemini-cli` action handles authentication robustly without the issues experienced by direct SDK usage.

## Extending and Customizing

-   **New LLM Questions**: Simply update the `LLM_QUESTIONS` list in `ciphr/config/config.py`.
-   **Different arXiv Categories**: Modify the `--tags` argument when running the script or the `ARXIV_TAGS` in `ciphr/config/config.py`.
-   **Output Format**: The `generate_markdown_table` function can be modified in either workflow approach.
-   **🆕 Custom Analysis**: The hybrid workflow's JSON intermediate format makes it easy to integrate with other analysis tools.

### Common arXiv Tags
- `hep-ex` - High Energy Physics - Experiment
- `hep-ph` - High Energy Physics - Phenomenology  
- `hep-th` - High Energy Physics - Theory
- `nucl-ex` - Nuclear Experiment
- `astro-ph` - Astrophysics
- `gr-qc` - General Relativity and Quantum Cosmology

## Troubleshooting

### Authentication Issues (GitHub Actions)
✅ **Resolved**: The hybrid workflow uses `google-github-actions/run-gemini-cli@v0` which handles authentication robustly.

### Empty LLM Results
✅ **Resolved**: Individual paper processing (analyze-1 through analyze-5) prevents batch processing issues that caused empty results.

### Common Issues
- **No papers found**: Check arXiv tags and date ranges
- **Duplicate papers**: System automatically skips papers already processed (check logs for "Skipping duplicate paper")
- **File permissions**: Ensure output directory is writable
- **Command not found**: Use `uv run ciphr-hybrid` (not `python -m ciphr.ciphr_hybrid`)

For detailed troubleshooting, see [HYBRID_WORKFLOW.md](HYBRID_WORKFLOW.md#troubleshooting).

## Quick Reference

### Available Commands

| Command | Purpose | Best For |
|---------|---------|----------|
| `uv run ciphr` | Original single-phase workflow | Local development, testing |
| `uv run ciphr-hybrid --mode collect` | Data collection only | Preparing data for analysis |
| `uv run ciphr-hybrid --mode process` | Process LLM results | After GitHub Actions LLM analysis |
| `uv run ciphr-hybrid --mode full` | Complete local workflow | Local testing with API keys |

### Workflow Comparison

| Feature | Original | Hybrid ✅ |
|---------|----------|--------|
| GitHub Actions reliability | ⚠️ Auth issues | ✅ Production ready |
| Empty results prevention | ⚠️ Batch processing issues | ✅ Individual processing |
| Error handling | Basic | ✅ Advanced |
| Debugging | Limited | ✅ Detailed logs |
| Maintenance | Manual SDK updates | ✅ Google maintained |
| Result parsing | Basic | ✅ Robust with delimiters |

### Migration Status

✅ **Migration Complete**: The repository has been fully migrated to the hybrid workflow.

**Current Commands:**
1. **Local testing**: `uv run ciphr-hybrid --mode collect --max_results 2 --verbose`
2. **GitHub Actions**: Uses hybrid workflow automatically
3. **Result processing**: `uv run ciphr-hybrid --mode process --verbose`
4. **Full local run**: `uv run ciphr-hybrid --mode full --max_results 5 --verbose` (requires API keys)

**For new users**: Start directly with the hybrid workflow - no migration needed.

## Example Output

The tool generates markdown tables like this:

```markdown
Paper Title | arXiv Link | What is the main physics phenomenon studied by this paper | Is this work related to dark matter searches? If yes, how? | Does this paper present experimental results? If yes, what is the name of the experimental apparatus?
----------- | ---------- | --------------------------------------------------------- | ---------------------------------------------------------- | -----------------------------------------------------------------------------------------------------
Probing Light Dark Matter with Cosmic Gravitational Focusing | [Link](http://arxiv.org/abs/2509.21213v1) | Light dark matter detection using cosmic gravitational focusing | Yes, this paper proposes a novel method to detect light dark matter particles | No, theoretical proposal for future experiments
Towards the Giant Radio Array for Neutrino Detection (GRAND) | [Link](http://arxiv.org/abs/2509.21306v1) | Ultra-high energy neutrino detection using radio arrays | Not directly, but neutrino detection can help constrain dark matter models | Yes, GRANDProto300 and GRAND@Auger prototypes
```

The questions analyzed can be customized in `ciphr/config/config.py`.

## License

This project is licensed under the Apache 2.0 License.
