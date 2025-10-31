# Contributing to CursorRules Architect V2

Thank you for considering contributing to CursorRules Architect! Your help is greatly appreciated. This guide explains how you can contribute to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Submitting Changes](#submitting-changes)
    - [Git Workflow](#git-workflow)
    - [Code Standards](#code-standards)
    - [Commit Messages](#commit-messages)
    - [Pull Request Guidelines](#pull-request-guidelines)
- [Development Setup](#development-setup)
  - [Prerequisites](#prerequisites)
  - [Installing Dependencies](#installing-dependencies)
  - [Setting Up API Keys](#setting-up-api-keys)
- [Running the Project](#running-the-project)
- [Testing](#testing)
- [Important Notes](#important-notes)
  - [Supported Models](#supported-models)
  - [Model Configuration](#model-configuration)
  - [Model Usage Restrictions](#model-usage-restrictions)

## Code of Conduct

By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful and considerate in all interactions.

## Getting Started

To get started with development, you'll need to set up your local environment.

### Prerequisites

- Python 3.8 or higher
- API keys for at least one of the following providers:
  - OpenAI API key with access to `o3`, `o4-mini`, or `gpt-4.1`
  - Anthropic API key with access to `claude-3-7-sonnet-20250219` 
  - DeepSeek API key with access to DeepSeek Reasoner
- Git

### Installing Dependencies

Clone the repository:

```bash
git clone https://github.com/SlyyCooper/cursorrules-architect.git
cd cursorrules-architect
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### Setting Up API Keys

Set your API keys as environment variables:

```bash
# Linux/macOS
export OPENAI_API_KEY='your-openai-api-key'
export ANTHROPIC_API_KEY='your-anthropic-api-key'
export DEEPSEEK_API_KEY='your-deepseek-api-key'

# Windows Command Prompt
set OPENAI_API_KEY=your-openai-api-key
set ANTHROPIC_API_KEY=your-anthropic-api-key
set DEEPSEEK_API_KEY=your-deepseek-api-key

# Windows PowerShell
$env:OPENAI_API_KEY='your-openai-api-key'
$env:ANTHROPIC_API_KEY='your-anthropic-api-key'
$env:DEEPSEEK_API_KEY='your-deepseek-api-key'
```

Alternatively, create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

**Important:** Ensure that your API keys have access to the required models. You can configure which models to use in `config/agents.py`.

## How to Contribute

Contributions can be in the form of bug reports, feature suggestions, or code changes.

### Reporting Bugs

If you encounter any bugs, please open an issue on GitHub with detailed information:

- Steps to reproduce the issue
- Expected and actual results
- Any relevant error messages or logs
- Your environment details (OS, Python version, package versions)

### Suggesting Features

We welcome feature suggestions! Please open an issue with:

- A clear and descriptive title
- A detailed description of the feature
- Any proposed implementation details

### Submitting Changes

#### Git Workflow

1. **Fork the Repository** on GitHub.
2. **Clone Your Fork**:

   ```bash
   git clone https://github.com/your-username/cursorrules-architect.git
   cd cursorrules-architect
   ```

3. **Create a Feature Branch**:

   ```bash
   git checkout -b feature/YourFeature
   ```

4. **Make Your Changes** and commit them.

5. **Push to Your Branch**:

   ```bash
   git push origin feature/YourFeature
   ```

6. **Open a Pull Request** on the original repository.

#### Code Standards

- **Python Style**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines.
- **Typing**: Use type hints where appropriate.
- **Imports**: Organize imports according to [PEP 8](https://www.python.org/dev/peps/pep-0008/#imports).
- **Documentation**: Include docstrings for functions, classes, and modules.
- **Architecture**: Follow the existing architectural patterns:
  - Use the `BaseArchitect` abstract class for new AI model providers
  - Keep prompts and logic separated
  - Ensure compatibility with the phase-based approach

#### Commit Messages

- Use descriptive commit messages.
- Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification when possible.

#### Pull Request Guidelines

- Ensure your code passes all tests.
- Address any merge conflicts.
- Provide a clear description of your changes in the pull request.
- If adding support for new models or providers, include documentation and examples.

## Development Setup

### Running the Project

You can run the main script using:

```bash
python main.py -p /path/to/your/project
```

To use the new architecture (recommended):

```bash
python main.py -p /path/to/your/project -n
```

### Testing

When adding new features or modifying existing ones, consider adding appropriate test cases. To run specific tests:

```bash
# Test a specific component
python -m unittest tests/test_your_component.py

# Run all tests
python -m unittest discover tests
```

## Important Notes

### Supported Models

CursorRules Architect V2 supports multiple AI models:

- **Anthropic**:
  - `claude-3-7-sonnet-20250219` (with or without reasoning)

- **OpenAI**:
  - `o3` (with low/medium/high reasoning)
  - `o4-mini` (with low/medium/high reasoning)
  - `gpt-4.1` (with temperature control)

- **DeepSeek**:
  - DeepSeek Reasoner (always with reasoning enabled)

### Model Configuration

You can configure which models are used for each phase by modifying the `MODEL_CONFIG` dictionary in `config/agents.py`. For example:

```python
MODEL_CONFIG = {
    "phase1": CLAUDE_WITH_REASONING,  # Use Claude with reasoning for Phase 1
    "phase2": O1_HIGH,                # Use OpenAI's o3 with high reasoning for Phase 2
    # etc.
}
```

### Model Usage Restrictions

Be mindful of API usage costs when developing and testing. Consider using mock responses or lower token budgets during development.

## Questions?

If you have any questions or need assistance, feel free to open an issue or reach out to the maintainers.

We look forward to your contributions!


