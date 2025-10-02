[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17244567.svg)](https://doi.org/10.5281/zenodo.17244567)
![GitHub Release-date](https://img.shields.io/github/release-date-pre/PRAkTIKal24/CIPhR?style=flat&color=blue)
![Release-version](https://img.shields.io/github/v/tag/PRAkTIKal24/CIPhR?include_prereleases&label=latest%20release&color=blue)
![GitHub repo size](https://img.shields.io/github/repo-size/PRAkTIKal24/CIPhR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![GitHub forks](https://img.shields.io/github/forks/PRAkTIKal24/CIPhR?style=flat&color=blue)

[![tests](https://github.com/PRAkTIKal24/CIPhR/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/PRAkTIKal24/CIPhR/actions)



# CIPhR: Crawl and Ingest Physics Research

> 🚀 **Status**: Production ready with unified workflow ✅  
> 🔧 **Latest**: Unified command structure with local and CI modes  
> 📅 **Updated**: October 2025 - Modernized with local mode and enhanced features

CIPhR is an automated tool designed to scrape particle physics research papers from arXiv, extract specific information using Large Language Model (LLM) analysis, and generate living markdown tables with research insights. This tool is built with Python, managed by `uv`, and supports both local development and automated CI/CD workflows.

## Features

- **🔍 arXiv Integration**: Search and download physics papers with smart duplicate detection
- **🤖 LLM Analysis**: Uses Google Gemini to answer customizable questions about papers
- **📊 Intelligent Tables**: Generates markdown tables with chronological sorting (newest first)
- **🔄 Multiple Modes**: Local development, data collection, processing, and CI workflows
- **🛡️ Robust Processing**: Error handling, duplicate detection, and question-based file management
- **🌐 WordPress Integration**: Automatic publishing to websites with responsive tables
- **💬 Mattermost ML4DM Bot**: Smart notifications for machine learning + dark matter papers
- **⚡ GitHub Actions Ready**: Automated daily execution with reliable authentication

## Quick Start

### 🏠 Local Usage (Recommended for Development)

```bash
# Install CIPhR
uv pip install -e .

# Set up API keys in .env file
FIRECRAWL_API_KEY=your_firecrawl_api_key
GEMINI_API_KEY=your_gemini_api_key

# Run complete local workflow (default mode)
uv run ciphr --tags hep-ex --max_results 5 --output_filename physics_papers.md

# Same as above (explicit local mode)
uv run ciphr --mode local --tags hep-ex --max_results 5
```

### ⚙️ Available Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **`local`** | Complete workflow with API keys | Local development, testing |
| `collect` | Data collection only | Preparing data for external LLM analysis |
| `process` | Process existing LLM results | After GitHub Actions LLM analysis |
| `full` | CI workflow (expects `run-gemini-cli`) | GitHub Actions automation |

### � Command Options

```bash
uv run ciphr [OPTIONS]

Options:
  --mode {local,collect,process,full}  Workflow mode (default: local)
  --tags TAGS                          arXiv categories (e.g., hep-ex,hep-ph)
  --max_results N                      Maximum papers to process (default: 5)
  --output_filename FILE               Output markdown file
  --output_dir DIR                     Output directory (default: output)
  --verbose                           Enable detailed logging
```

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:PRAkTIKal24/CIPhR.git
   cd CIPhR
   ```

2. **Install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

3. **Configure API Keys**:
   Create a `.env` file:
   ```env
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Test installation**:
   ```bash
   uv run ciphr --mode local --max_results 1 --verbose
   ```

## �🚀 Mattermost ML4DM Bot Integration

CIPhR includes intelligent Mattermost integration that automatically detects papers using **Machine Learning for Dark Matter (ML4DM)** research and posts notifications to your Mattermost channels.

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
│       └── ciphr.yml             # GitHub Actions workflow
├── ciphr/
│   ├── config/
│   │   └── config.py             # Configuration for API keys, arXiv tags, and LLM questions
│   ├── src/
│   │   ├── arxiv_scraper.py      # Handles arXiv searching and PDF downloading
│   │   ├── llm_analyzer.py       # LLM analysis for local mode
│   │   ├── data_processor.py     # Data collection for CI workflows
│   │   ├── result_processor.py   # Result processing and table generation
│   │   ├── mattermost_notifier.py # 🤖 ML4DM detection and Mattermost posting
│   │   └── wordpress_publisher.py # 📝 WordPress integration for automated publishing
│   ├── ciphr.py                  # 🎯 Main unified command (supports local and CI modes)
│   └── ciphr_legacy.py           # Legacy single-phase workflow (backup)
├── output/                       # Generated research insights and intermediate files
├── tests/                        # Unit tests for the project
├── pyproject.toml               # Python project configuration (uv-based)
├── README.md                    # This file
├── HYBRID_WORKFLOW.md           # Detailed workflow documentation
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

### 🚀 Local Development Mode (Recommended for development)

For local development with immediate LLM analysis:

```bash
uv run ciphr --mode local --tags hep-ex --max_results 10 --output_dir output --output_filename hepex.md --verbose
```

### 🔧 CI/CD Workflow Modes

For production GitHub Actions workflows, use these modes:

**Data Collection (Phase 1):**
```bash
uv run ciphr --mode collect --tags hep-ex --max_results 10 --output_dir output --output_filename hepex.md --verbose
```

**Result Processing (Phase 3 - after LLM analysis):**
```bash
uv run ciphr --mode process --output_dir output --output_filename hepex.md --verbose
```

**Full Workflow (Local with API keys):**
```bash
uv run ciphr --mode full --tags hep-ex --max_results 10 --output_dir output --output_filename hepex.md --verbose
```

> ⚠️ **Note**: The `--mode local` and `--mode full` require GEMINI_API_KEY for LLM analysis. For production CI/CD, use the GitHub Actions workflow which handles LLM analysis via dedicated actions. See [ciphr.yml](https://github.com/PRAkTIKal24/CIPhR/blob/main/.github/workflows/ciphr.yml).

> 📖 **For detailed workflow instructions, see [HYBRID_WORKFLOW.md](HYBRID_WORKFLOW.md)**

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

### ✅ Production CI/CD Workflow

The current `.github/workflows/ciphr.yml` uses a three-phase approach:

1. **Data Collection**: Scrapes arXiv and processes PDFs using `uv run ciphr --mode collect`
2. **LLM Analysis**: Individual paper analysis using `google-github-actions/run-gemini-cli@v0` (analyze-1 through analyze-5 steps)
3. **Result Processing**: Combines individual results and generates final markdown tables using `uv run ciphr --mode process`

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
-   **Output Format**: The `generate_markdown_table` function can be modified in `ciphr/src/result_processor.py`.
-   **Custom Analysis**: The JSON intermediate format makes it easy to integrate with other analysis tools.

### Common arXiv Tags
- `hep-ex` - High Energy Physics - Experiment
- `hep-ph` - High Energy Physics - Phenomenology  
- `hep-th` - High Energy Physics - Theory
- `nucl-ex` - Nuclear Experiment
- `astro-ph` - Astrophysics
- `gr-qc` - General Relativity and Quantum Cosmology

## Troubleshooting

### Common Issues
- **No papers found**: Check arXiv tags and date ranges
- **Duplicate papers**: System automatically skips papers already processed (check logs for "Skipping duplicate paper")
- **File permissions**: Ensure output directory is writable
- **Missing dependencies**: Run `uv sync` to install all required packages

For detailed troubleshooting, see [HYBRID_WORKFLOW.md](HYBRID_WORKFLOW.md#troubleshooting).

## Quick Reference

### Available Commands

| Command | Purpose | Best For |
|---------|---------|----------|
| `uv run ciphr --mode local` | Complete local workflow with LLM | Development and testing |
| `uv run ciphr --mode collect` | Data collection only | CI/CD phase 1 |
| `uv run ciphr --mode process` | Process LLM results | CI/CD phase 3 |
| `uv run ciphr --mode full` | Complete workflow (legacy mode) | Local testing |

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
