# CIPhR Hybrid Workflow Guide

## Overview

CIPhR now supports a hybrid workflow that combines your custom physics research processing with Google's robust `run-gemini-cli` GitHub Action. This approach solves authentication issues while maintaining all your domain-specific functionality.

## 🚀 Why Use the Hybrid Approach?

The hybrid workflow was developed to address authentication issues when running CIPhR in GitHub Actions environments. The original approach had problems with Google AI SDK auto-detecting GCP environments and trying to use Vertex AI instead of the Google AI API.

### Benefits

- ✅ **Solves Authentication Issues**: Uses Google's official action that handles GCP environment detection properly
- ✅ **Maintains Your Logic**: All domain-specific code (arXiv processing, PDF handling, markdown generation) is preserved  
- ✅ **Better Error Handling**: The `run-gemini-cli` action has mature error handling and logging
- ✅ **More Reliable**: Maintained by Google, less likely to break with environment changes
- ✅ **Flexible**: Can easily switch between different Gemini models or authentication methods

## 🔧 How It Works

The hybrid approach splits the workflow into three phases:

### Phase 1: Data Collection
```bash
uv run ciphr-hybrid --mode collect --output_dir output --output_filename hepex.md --tags hep-ex
```

**What it does:**
- Scrapes arXiv papers based on your tags
- Downloads and extracts PDF content using pypdf
- Combines abstract + PDF text for each paper
- Saves structured data to `papers_data.json`
- Creates analysis prompts for Gemini in `analysis_prompts.json`
- Handles duplicate detection by checking existing output files

**Output files:**
- `papers_data.json` - Contains paper metadata, abstracts, and PDF content
- `analysis_prompts.json` - Contains questions and instructions for LLM analysis

### Phase 2: LLM Analysis (GitHub Actions)
Uses the `google-github-actions/run-gemini-cli@v0` action to:
- Process all papers in a single, efficient API call
- Use Google's official authentication (no more auth headaches!)
- Return structured JSON results
- Handle rate limiting and error recovery automatically

### Phase 3: Result Processing
```bash
uv run ciphr-hybrid --mode process --output_dir output --output_filename hepex.md
```

**What it does:**
- Parses LLM results intelligently (handles various JSON formats)
- Maps answers back to your configured questions
- Generates final markdown table with proper formatting
- Handles file naming (appends or creates new files based on question changes)
- Maintains all existing features like duplicate detection

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install CIPhR with hybrid support
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Configure API Keys

The hybrid workflow only requires the Gemini API key for LLM analysis:

**For GitHub Actions:**
- Go to your repository's **Settings > Secrets and variables > Actions**
- Add `GEMINI_API_KEY` with your Google AI Studio API key
- Add `FIRECRAWL_API_KEY` if using Firecrawl features

**For local testing:**
Create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 3. Workflow Configuration

The hybrid workflow is automatically configured in `.github/workflows/main.yml`. It runs three jobs:

1. **collect_data** - Data collection phase
2. **analyze_papers** - LLM analysis using run-gemini-cli
3. **process_results** - Result processing and markdown generation

## 📋 Usage Examples

### Local Testing

**Test data collection only:**
```bash
uv run ciphr-hybrid --mode collect --max_results 2 --tags hep-ex --output_dir test_output --verbose
```

**Process existing results:**
```bash
# Assuming you have papers_data.json and llm_results.txt
uv run ciphr-hybrid --mode process --output_dir test_output --output_filename results.md --verbose
```

**Full local workflow (requires API keys):**
```bash
uv run ciphr-hybrid --mode full --max_results 5 --tags hep-ph --output_dir output --output_filename physics.md
```

### GitHub Actions

The workflow runs automatically:
- **Scheduled**: Daily at 00:00 UTC
- **Manual**: Via workflow_dispatch in GitHub Actions tab

**Customizing the workflow:**
Edit `.github/workflows/main.yml` to change:
- Schedule timing
- arXiv tags (`--tags hep-ex` → `--tags hep-ph,nucl-ex`)
- Output filename
- Maximum results

## 🔍 File Structure

```
output/
├── papers_data.json          # Collected paper data
├── analysis_prompts.json     # LLM analysis instructions  
├── llm_results.txt          # Raw LLM output from run-gemini-cli
└── hepex.md                 # Final markdown table
```

### papers_data.json Format
```json
[
  {
    "title": "Paper title",
    "arxiv_url": "http://arxiv.org/abs/2024.12345",
    "abstract": "Paper abstract text",
    "pdf_content": "Extracted PDF text",
    "combined_content": "Abstract + PDF combined",
    "authors": ["Author 1", "Author 2"],
    "published": "2024-09-26T10:00:00",
    "categories": ["hep-ex"]
  }
]
```

## 🎯 Configuration

### Questions Configuration
Edit `ciphr/config/config.py` to modify the questions asked about each paper:

```python
LLM_QUESTIONS = [
    "What is the main physics phenomenon studied by this paper",
    "Is this work related to dark matter searches? If yes, how?",
    "Does this paper present experimental results? If yes, what is the name of the experimental apparatus?",
    # Add your custom questions here
]
```

### arXiv Tags
Common physics tags:
- `hep-ex` - High Energy Physics - Experiment
- `hep-ph` - High Energy Physics - Phenomenology  
- `hep-th` - High Energy Physics - Theory
- `nucl-ex` - Nuclear Experiment
- `astro-ph` - Astrophysics
- `gr-qc` - General Relativity and Quantum Cosmology

## 🐛 Troubleshooting

### Common Issues

**1. No papers found**
- Check if arXiv tags are correct
- Verify date ranges (recent papers may not be available immediately)
- Check network connectivity

**2. LLM analysis fails**
- Verify `GEMINI_API_KEY` is correctly set in GitHub secrets
- Check API quotas and rate limits
- Review GitHub Actions logs for specific error messages

**3. Result processing errors**
- Ensure `papers_data.json` exists from data collection phase
- Check `llm_results.txt` format (should contain JSON array)
- Verify file permissions and disk space

### Debug Mode
Add `--verbose` flag for detailed logging:
```bash
uv run ciphr-hybrid --mode collect --verbose
```

### Manual Recovery
If a phase fails, you can run individual phases:
```bash
# Re-run only data collection
uv run ciphr-hybrid --mode collect --output_dir output

# Re-run only result processing (after fixing LLM results)  
uv run ciphr-hybrid --mode process --output_dir output
```

## 🔄 Migration from Original CIPhR

### Backward Compatibility
- Original `uv run ciphr` command still works
- Old workflows continue to function
- Same output format and file structure

### Gradual Migration
1. Test hybrid workflow with `--mode collect` locally
2. Update GitHub Actions to use hybrid workflow
3. Monitor results for a few runs
4. Gradually phase out original workflow if desired

### Key Differences
| Original CIPhR | Hybrid CIPhR |
|----------------|---------------|
| Single-phase processing | Three-phase processing |
| Direct Gemini API calls | Uses run-gemini-cli action |
| Authentication issues in GH Actions | Robust authentication |
| Synchronous processing | Parallelizable phases |

## 📈 Performance Considerations

### Efficiency Improvements
- **Batch processing**: All papers analyzed in single LLM call
- **Parallel phases**: Data collection and result processing can run independently
- **Caching**: Intermediate files allow resuming from failures

### Resource Usage
- **Memory**: Similar to original (PDFs processed one at a time)
- **Disk**: Temporary JSON files (cleaned up automatically)
- **API calls**: More efficient (batch processing reduces calls)

## 🤝 Contributing

When contributing to the hybrid workflow:

1. **Test locally first**: Use `--mode collect` and `--mode process` 
2. **Maintain compatibility**: Ensure changes work with both workflows
3. **Update documentation**: Keep this guide current with changes
4. **Add tests**: Include tests for new features in both modes

## 📚 Advanced Usage

### Custom LLM Prompts
Modify `ciphr/src/data_processor.py` to customize the analysis prompt:

```python
def create_analysis_prompts(self, questions: List[str], output_file: str = "analysis_prompts.json") -> str:
    prompts_data = {
        "questions": questions,
        "instructions": """Your custom instructions here..."""
    }
```

### Integration with Other Tools
The JSON output format makes it easy to integrate with other analysis tools:

```python
import json

# Load CIPhR results
with open('output/papers_data.json', 'r') as f:
    papers = json.load(f)

# Process with your tools
for paper in papers:
    # Your custom analysis here
    analyze_paper_further(paper)
```

## 🆘 Support

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/PRAkTIKal24/CIPhR/issues)
2. Review GitHub Actions logs for detailed error messages  
3. Test individual phases locally with `--verbose` flag
4. Create an issue with:
   - Error messages
   - Configuration used
   - Sample input data (if possible)

The hybrid workflow represents a significant improvement in reliability and maintainability while preserving all the physics research functionality you need!