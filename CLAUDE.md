# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SE-Agent is a Self-Evolution framework that enables LLM-based agents to optimize their reasoning processes iteratively. It's built on top of SWE-Agent and focuses on trajectory optimization for solving software engineering problems through revision, recombination, and refinement operations.

## Development Setup

### Environment Setup
```bash
# Create conda environment (Python 3.12 required)
conda env create -n SWE python=3.12
conda activate SWE

# Install in editable mode (required)
python -m pip install --upgrade pip && pip install --editable .

# Verify installation
sweagent --help
```

### API Configuration
Required API keys in `.env` file:
```
DEEPSEEK_API_KEY=<your_key>
ANTHROPIC_API_KEY=<your_key>
OPENAI_API_KEY=<your_key>
```

## Common Development Commands

### Testing
```bash
# Run main test suite
pytest

# Run SE framework tests
python SE/test/run_operator_tests.py

# Test specific components
python SE/test/test_operators.py
python SE/test/test_unified_data_interface.py
python SE/test/test_traj_pool.py

# API integration tests
python SE/test/api_test.py
python SE/test/llm_integration/test_llm_integration.py
```

### Running SE Framework
```bash
# Demo mode (no API calls)
python SE/basic_run.py --mode demo

# Execute experiments
python SE/basic_run.py --mode execute

# With custom config
python SE/basic_run.py --config SE/configs/se_configs/test_deepseek_se.yaml --mode execute
```

### SWE-Agent Commands
```bash
# Single instance test
sweagent run \
  --agent.model.name=deepseek/deepseek-chat \
  --agent.model.per_instance_cost_limit=2.00 \
  --env.repo.github_url=https://github.com/SWE-agent/test-repo \
  --problem_statement.github_url=https://github.com/SWE-agent/test-repo/issues/1

# Batch processing
sweagent run-batch \
  --config config/default.yaml \
  --agent.model.name deepseek/deepseek-chat \
  --instances.slice :1
```

### Code Quality
```bash
# Linting with ruff (configured in pyproject.toml)
ruff check .
ruff format .

# Type checking (if mypy is available)
mypy sweagent/
```

## Architecture Overview

### Core Components

**SE Framework** (`SE/`):
- `basic_run.py`: Multi-iteration experiment runner
- `core/swe_iterator.py`: SWE-Agent iteration wrapper
- `operators/`: Self-evolution operators (revision, recombination, refinement)
- `configs/`: Experiment configurations

**SWE-Agent Base** (`sweagent/`):
- `agent/`: Core agent implementations
- `environment/`: Repository interaction layer
- `run/`: Execution orchestration
- `tools/`: Agent tools and commands

**Trajectory System**:
- Trajectory files (.traj) contain full execution traces
- Compressed trajectories (.tra) save 75-87% storage
- Problem files (.problem) extracted from trajectories
- Prediction files (.pred) contain final answers

### Key Data Flow

1. **Instance Loading**: JSON instances → Problem statements
2. **Trajectory Generation**: SWE-Agent execution → .traj files
3. **SE Operations**: Operators analyze/modify trajectories
4. **Iteration**: Multiple runs with different strategies
5. **Output**: Compressed results in timestamped directories

### Operator System

Operators implement trajectory optimization:
- **Base operators**: `SE/operators/base.py`
- **Registry**: `SE/operators/registry.py` for operator management
- **Templates**: Extensible operator framework for custom strategies

## Configuration Files

### SE Configs (`SE/configs/se_configs/`)
Define multi-iteration experiments:
```yaml
model:
  name: "deepseek/deepseek-chat"
  api_key: "your-key"

strategy:
  iterations:
    - base_config: "test_claude"
      operator: null
    - base_config: "baseconfig1" 
      operator: "Crossover"
```

### Base Configs (`SE/configs/base_configs/`)
SWE-Agent configuration templates with different strategies.

## Important File Locations

- **Main entry**: `SE/basic_run.py`
- **Core iterator**: `SE/core/swe_iterator.py`
- **Operator base**: `SE/operators/base.py`
- **Test suite**: `SE/test/run_operator_tests.py`
- **Configuration**: `SE/configs/` (all experiment configs)
- **Output**: `SE/trajectories/` (experiment results)

## Development Workflow

1. **Working Directory**: Always run SE commands from project root
2. **Configuration First**: Create/modify configs in `SE/configs/se_configs/`
3. **Test Changes**: Run `python SE/test/run_operator_tests.py`
4. **Experiment**: Use demo mode first, then execute mode
5. **Analysis**: Check outputs in `SE/trajectories/timestamp_dir/`

## Output Structure

```
SE/trajectories/experiment_YYYYMMDD_HHMMSS/
├── iteration_1/
│   ├── instance_name/
│   │   ├── instance.traj     # Full trajectory
│   │   ├── instance.tra      # Compressed trajectory  
│   │   ├── instance.problem  # Problem description
│   │   └── instance.pred     # Prediction result
│   └── preds.json           # Batch results
├── iteration_2/
└── se_framework.log         # Framework logs
```

## Package Dependencies

Core dependencies from `pyproject.toml`:
- `litellm`: LLM API abstraction
- `simple-parsing`: Configuration parsing
- `rich`: Terminal output formatting
- `GitPython`: Git operations
- `swe-rex>=1.2.0`: SWE-Agent extensions
- `pydantic`: Data validation

Development dependencies include `pytest`, `ruff`, `pre-commit`.