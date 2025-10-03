[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17257638.svg)](https://doi.org/10.5281/zenodo.17257638)
![GitHub Release-date](https://img.shields.io/github/release-date-pre/PRAkTIKal24/CIPhR?style=flat&color=blue)
![Release-version](https://img.shields.io/github/v/tag/PRAkTIKal24/CIPhR?include_prereleases&label=latest%20release&color=blue)
![GitHub repo size](https://img.shields.io/github/repo-size/PRAkTIKal24/CIPhR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![GitHub forks](https://img.shields.io/github/forks/PRAkTIKal24/CIPhR?style=flat&color=blue)

[![tests](https://github.com/PRAkTIKal24/CIPhR/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/PRAkTIKal24/CIPhR/actions)



# CIPhR: Crawl and Ingest Physics Research

> 🚀 **Status**: Production ready with unified workflow ✅  
> 🔧 **Latest**: Added a smart search expansion feature to search beyond previously analyzed papers
> 📅 **Updated**: October 2025 - Modernized with local mode and enhanced features

CIPhR is an automated tool designed to scrape particle physics research papers from arXiv, extract specific information using Large Language Model (LLM) analysis, and generate living markdown tables with research insights. This tool is built with Python, managed by `uv`, and supports both local development and automated CI/CD workflows.

## 📑 Table of Contents

- [Features](#features)
- [🔧 Installation and Setup](#-installation-and-setup)
- [Quick Start](#quick-start)
  - [🏠 Local Usage (Recommended for Development)](#-local-usage-recommended-for-development)
  - [Configuration](#configuration)
  - [Command Options](#-command-options)
  - [⚙️ Available Modes](#️-available-modes)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [🚀 Local Development Mode](#-local-development-mode-recommended-for-development)
  - [🔧 CI/CD Workflow Modes](#-cicd-workflow-modes)
- [GitHub Actions Automation](#github-actions-automation)
  - [✅ Production CI/CD Workflow](#-production-cicd-workflow)
  - [Setting up API Keys and Webhooks](#setting-up-api-keys-and-webhooks-in-github-secrets)
- [🚀 Mattermost ML4DM Bot Integration](#-mattermost-ml4dm-bot-integration)
- [Extending and Customizing](#extending-and-customizing)
- [Troubleshooting](#troubleshooting)
- [Quick Reference](#quick-reference)
- [Example Output](#example-output)
- [License](#license)

## Features

- **🔍 arXiv Integration**: Search and download physics papers with smart duplicate detection
- **🤖 LLM Analysis**: Uses Google Gemini to answer customizable questions about papers
- **📊 Intelligent Tables**: Generates markdown tables with chronological sorting (newest first)
- **🔄 Multiple Modes**: Local development, data collection, processing, and CI workflows
- **🛡️ Robust Processing**: Error handling, duplicate detection, and question-based file management
- **🧠 Smart Expansion Search**: Automatically expands search when initial results are stale/duplicates, finding fresh papers while respecting user limits and rate constraints
- **📝 Smart Content Processing**: Automatic reference stripping and conclusions extraction for optimal LLM analysis
- **🎯 Enhanced Paper Coverage**: 50K character limit ensures complete paper analysis (15x improvement)
- **🌐 WordPress Integration**: Automatic publishing to websites with responsive tables
- **💬 Mattermost ML4DM Bot**: Smart notifications for machine learning + dark matter papers
- **⚡ GitHub Actions Ready**: Automated daily execution with reliable authentication

## 🔧 Installation and Setup

1.  **Install `uv` (if not already installed)**:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ```

2. **Clone the repository**:
   ```bash
   git clone git@github.com:PRAkTIKal24/CIPhR.git
   cd CIPhR
   ```

3.  **Create a virtual environment and install dependencies**:

    ```bash
    uv sync --refresh
    ```

    If you want to develop new features, install the `dev-dependencies` as well:

    ```bash
    uv sync --group dev
    ```

4. **Configure API Keys**:
   Create a `.env` file at the CIPhR root (same directory level as `pyproject.toml`) and enter the following in it with your own API_KEYs:
   ```env
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Test installation**:
   ```bash
   uv run ciphr --help
   ```

## Quick Start

### 🏠 Local Usage (Recommended for Development)

```bash
# Run complete local workflow (default mode)
uv run ciphr --tags hep-ex --max_results 5 --output_filename my_output.md --verbose
```

```bash
# Same as above (explicit local mode, output directory declarations)
uv run ciphr --mode local --tags hep-ex --max_results 5 --output_dir output --output_filename my_output.md --verbose
```


### Configuration

The `config/config.py` file allows you to customize default settings:

#### 🔑 API Configuration
-   `FIRECRAWL_API_KEY`: Your Firecrawl API key (loaded from `.env`).
-   `GEMINI_API_KEY`: Your Gemini API key (loaded from `.env`).

#### 🤖 LLM Questions Configuration
-   `LLM_QUESTIONS`: A list of strings, where each string is a question you want the LLM to answer for each paper. These questions appear in the main research output table.
-   `ML4DM_DETECTION_QUESTION`: Additional question used specifically for ML4DM detection and Mattermost notifications (not included in the main output table).

#### 📊 Question Functions
-   `get_llm_questions()`: Returns questions for the main research table (used in local and CI modes).
-   `get_ci_analysis_questions()`: Returns all questions including ML4DM detection (used only in CI workflows).

#### 🔍 Search Configuration
-   `ARXIV_TAGS`: Default arXiv categories (e.g., "hep-ph", "hep-ex").
-   `MAX_ARXIV_RESULTS`: Default maximum number of results to process.
-   `MAX_EXPANSION_RESULTS`: Maximum papers to search when expanding for duplicates (default: 25).

#### 📝 Content Processing
-   `MAX_CONTENT_LENGTH_FOR_LLM`: Maximum characters from paper content for LLM analysis (50K allows ~100% coverage).
-   `MAX_CONCLUSIONS_LENGTH`: Maximum characters to extract from conclusions section (3K).
-   `STRIP_REFERENCES`: Whether to remove references/bibliography sections (default: True).
-   `LOG_PREVIEW_LENGTH`: Length of content preview in logs (500 chars).
-   `ERROR_MESSAGE_LENGTH`: Length of truncated error messages (100 chars).


### � Command Options

```bash
uv run ciphr [OPTIONS]

Options:
  --mode {local,collect,process,full}  Workflow mode (default: local)
  --tags TAGS                          arXiv categories (e.g., hep-ex,hep-ph)
  --max_results N                      Maximum papers to process (default: 5)
  --output_filename FILE               Output markdown file
  --output_dir DIR                     Output directory (default: output)
  --verbose                            Enable detailed logging
```
You can also use the following to see these options in the command line:

```bash
uv run ciphr --help
```

### ⚙️ Available Modes

> ⚠️ **Note**: Only the `local` mode is recommended for running locally. Other modes are mainly intended for CI/CD deployment!

| Mode | Description | Use Case |
|------|-------------|----------|
| **`local`** | Complete workflow with API keys | Local development, testing |
| `collect` | Data collection only | Preparing data for external LLM analysis |
| `process` | Process existing LLM results | After GitHub Actions LLM analysis |
| `full` | CI workflow (expects `run-gemini-cli`) | GitHub Actions automation |

## Project Structure

```
CIPhR/
├── .github/
│   └── workflows/
│       └── ciphr.yml             # GitHub Actions workflow with smart expansion & ML4DM detection
├── ciphr/
│   ├── config/
│   │   └── config.py             # 🔧 Enhanced configuration with separated question sets and content processing
│   ├── src/
│   │   ├── arxiv_scraper.py      # 🔍 arXiv searching and PDF downloading with smart duplicate detection
│   │   ├── llm_analyzer.py       # 🤖 LLM analysis for local mode
│   │   ├── data_processor.py     # 📊 Data collection with smart expansion for CI workflows
│   │   ├── result_processor.py   # 📝 Result processing and table generation with question management
│   │   ├── mattermost_notifier.py # 🤖 ML4DM detection and Mattermost posting
│   │   ├── wordpress_publisher.py # 📝 WordPress integration for automated publishing
│   │   └── utils.py              # 🛠️ Utility functions for modular architecture
│   ├── ciphr_hybrid.py           # 🎯 Main unified command (supports local and CI modes)
│   └── __main__.py               # 🚀 Entry point for command execution
├── output/                       # 📂 Generated research insights and intermediate files
├── tests/                        # 🧪 Comprehensive unit tests for all modules
├── pyproject.toml               # 📦 Python project configuration (uv-based)
├── README.md                    # 📖 This file
├── HYBRID_WORKFLOW.md           # 📋 Detailed workflow documentation
└── .env                         # 🔐 Environment variables for API keys (local development)
```

## Usage

### 🚀 Local Development Mode (Recommended for development)

For local development with immediate LLM analysis:

```bash
uv run ciphr --mode local --tags hep-ex --max_results 5 --output_dir output --output_filename hepex.md --verbose
```

#### 📊 **Recommended Approach: 5 Papers Per Run**

The `--max_results 5` parameter is **strongly recommended** for both local and CI workflows to avoid hitting Gemini API rate limits. 

**✅ For processing more than 5 papers, use multiple runs with shell scripts:**

```bash
#!/bin/bash
# Example: Process 15 papers total (3 runs of 5 papers each)
for i in {1..3}; do
  echo "Run $i: Processing papers..."
  uv run ciphr --mode local --tags hep-ex --max_results 5 --output_filename hepex.md --verbose
  sleep 30  # Optional: Brief pause between runs
done
```

**🧠 Smart Expansion Benefits:**
- **Automatic Discovery**: Each run uses smart expansion to find the newest available papers
- **Duplicate Avoidance**: Built-in duplicate detection ensures no paper is processed twice
- **Rate Limit Compliance**: 5 papers per run stays well within API limits
- **Fresh Content**: Later runs automatically discover papers missed by earlier runs

**⚙️ Advanced Configuration:**
If you need to adjust the smart expansion search capacity, modify `MAX_EXPANSION_RESULTS` in `ciphr/config/config.py` (default: 25 papers). This controls how many papers the system searches through to find your requested 5 unique papers.

**⚠️ Why Not Higher `--max_results`?**
- Values above 5 frequently trigger Gemini rate limits
- Large batches can cause timeouts and incomplete analysis
- Multiple smaller runs are more reliable and provide better error recovery

### 🔧 CI/CD Workflow Modes

For production GitHub Actions workflows, use these modes:

**Data Collection (Phase 1):**
```bash
uv run ciphr --mode collect --tags hep-ex --max_results 5 --output_dir output --output_filename hepex.md --verbose
```

**LLM Analysis (Phase 2):**
See [ciphr.yml](https://github.com/PRAkTIKal24/CIPhR/blob/main/.github/workflows/ciphr.yml) for instructions on how to use `run-gemini-cli` independently for this phase.

**Result Processing (Phase 3 - after LLM analysis):**
```bash
uv run ciphr --mode process --output_dir output --output_filename hepex.md --verbose
```

> ⚠️ **Note**: The `--mode local` and `--mode full` require GEMINI_API_KEY for LLM analysis. For production CI/CD, use the GitHub Actions workflow which handles LLM analysis via dedicated actions. See [ciphr.yml](https://github.com/PRAkTIKal24/CIPhR/blob/main/.github/workflows/ciphr.yml).

> 📖 **For detailed workflow instructions, see [HYBRID_WORKFLOW.md](HYBRID_WORKFLOW.md)**

## GitHub Actions Automation

### ✅ Production CI/CD Workflow

The current `.github/workflows/ciphr.yml` uses a modern three-phase approach with smart expansion:

1. **Data Collection**: Scrapes arXiv with smart expansion logic using `uv run ciphr --mode collect`
   - 🧠 **Smart Expansion**: Automatically searches 3x more papers when duplicates are found
   - 🎯 **User Limit Respect**: Always returns exactly the number of papers requested (max_results)
   - 🔍 **Enhanced Coverage**: Searches up to 25 papers to find fresh, unique content
   
2. **LLM Analysis**: Individual paper analysis using `google-github-actions/run-gemini-cli@v0` (analyze-1 through analyze-5 steps)
   - 🔧 **Individual Processing**: Each paper analyzed separately for maximum reliability
   - 🎛️ **Dynamic Scaling**: Only runs analysis steps for papers actually found (1-5 papers)
   - 📊 **Separated Questions**: Uses CI-specific questions including ML4DM detection
   
3. **Result Processing**: Combines individual results and generates final outputs using `uv run ciphr --mode process`
   - 📝 **Clean Tables**: Only processes successfully analyzed papers
   - 🤖 **ML4DM Detection**: Automatically posts to Mattermost when ML papers are found
   - 📊 **Question Separation**: Main table uses research questions, notifications use ML4DM detection

**Benefits:**
- ✅ **Smart Paper Discovery**: Finds fresh papers even when initial search returns stale results
- ✅ **No Empty Results**: Individual processing prevents failed LLM analysis
- ✅ **Reliable Authentication**: GitHub-maintained actions for stable API access
- ✅ **Dynamic Scaling**: Handles 1-5 papers automatically without hardcoding
- ✅ **Enhanced Logging**: Detailed logs for debugging and monitoring
- ✅ **Question Management**: Separated concerns for research vs notification questions
- 🤖 **Intelligent ML4DM Detection**: Smart pattern matching for machine learning papers

**Schedule:** 
- Runs every day at 07:00 UTC
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
