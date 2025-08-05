<div align="center">

<table border="0">
  <tr>
    <td><img src="static/img/logo.png" alt="SE-Agent Logo" width="200"/></td>
    <td><h1>SE-Agent: Self-Evolution Trajectory Optimization in Multi-Step Reasoning with LLM-Based Agents</h1></td>
  </tr>
</table>

</div>

<p align="center">
  <strong>🏆 State-of-the-Art Performance on SWE-bench Verified</strong><br>
  <strong>🚀 Up to +112% Performance Gain</strong><br>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python"></a>
  <a href="https://www.arxiv.org/abs/2508.02085"><img src="https://img.shields.io/badge/Paper-arXiv-red.svg" alt="Paper"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <a href="https://www.swebench.com"><img src="https://img.shields.io/badge/SWE--bench-Verified%20%231-gold.svg" alt="SWE-bench"></a>
</p>

</div>

---

## 🎯 What is SE-Agent?

SE-Agent is a **meta-learning framework** that enables LLM-based agents to **evolve their problem-solving strategies** through iterative self-improvement. Unlike traditional approaches that rely on numerical optimization, SE-Agent operates at the **cognitive strategy level**, analyzing failure patterns and generating fundamentally different solution approaches.

<div align="center">
<img src="static/img/framework.jpg" alt="SE-Agent Framework" width="500px" />
</div>

### 🔥 Key Breakthrough

**From Numerical Optimization → Semantic Strategy Evolution**

Traditional methods like MCTS explore solution spaces through random sampling and numerical rewards. SE-Agent analyzes **why** approaches fail and generates **architecturally different** strategies, leading to breakthrough performance gains.

### 📊 Performance Results

#### 🏆 SWE-bench Verified Evaluation: State-of-the-Art Performance!
SE-Agent ranks **first among open-source frameworks** on SWE-bench Verified.

<div align="center">
<img src="static/img/ranking_new.jpg" alt="Open-Source Framework Comparison" width="600px" />
</div>

#### ✨ Performance Comparison: Leading with Significant Gains!
<div align="center">
<img src="static/img/table1.png" alt="SE-Agent Framework Illustration" width="600px" />
</div>

## ⚡ Quick Start

Get SE-Agent running in **30 seconds**:

```bash
# 1. Clone and install
git clone https://github.com/JARVIS-Xs/SE-Agent.git
cd SE-Agent
pip install -e .

# 2. Set up API key
echo "DEEPSEEK_API_KEY=your_key_here" > .env

# 3. Run demo (no API calls)
python SE/basic_run.py --mode demo

# 4. Run your first experiment
python SE/basic_run.py --mode execute
```

**Expected Output:**
```
✅ SE-Agent initialized successfully
🔄 Starting self-evolution with 3 iterations  
📈 Performance gain: +67% over baseline
```

<details>
<summary>🔧 <strong>Need help with setup?</strong></summary>

**Alternative Installation:**
```bash
conda create -n SE python=3.12
conda activate SE  
pip install -e .
```

**Environment Variables:**
```bash
# Required (choose one)
export DEEPSEEK_API_KEY="your_key"
export OPENAI_API_KEY="your_key" 
export ANTHROPIC_API_KEY="your_key"
```

</details>

## 🧠 How SE-Agent Works

SE-Agent implements **three core self-evolution operations** that transform how agents approach problem-solving:

### 🔄 Three Core Operations

#### 1. **🔧 Revision** - *Failure-Driven Strategy Generation*
Analyzes individual failed trajectories through **deep self-reflection** and **targeted improvement**. Goes beyond simple retries by identifying fundamental approach limitations and creating **architecturally orthogonal** problem-solving paradigms. This involves analyzing a single trajectory to identify errors, inefficiencies, or conceptual blind spots, then prompting the agent to generate completely different solution approaches that address these specific limitations.

#### 2. **🤝 Recombination** - *Cross-Trajectory Knowledge Synthesis*  
Creates novel trajectories by **intelligently combining strengths** from multiple existing solution paths. This is where **cross-trajectory inspiration** primarily occurs - SE-Agent intelligently selects high-performing segments from different trajectories and merges them to construct superior approaches. The process explicitly leverages the **interdependence of various attempts**, allowing successes in one area to compensate for shortcomings in others, enabling **1+1>2** synergistic effects that transcend individual trajectory limitations.

#### 3. **✨ Refinement** - *Risk-Aware Trajectory Optimization*
Optimizes promising trajectories by **eliminating redundancies** and **enhancing efficiency** using insights from the entire trajectory pool. After new trajectories are formed, this step further hones them by removing unnecessary steps, streamlining action sequences, and incorporating **risk-aware guidance** that prevents systematic blind spots and failure modes learned from the collective exploration history.

<div align="center">
<img src="static/img/se-agent-case-study.png" alt="SE-Agent Case Study" width="600px" />
</div>


## 💻 Usage Examples

### Basic Self-Evolution Experiment

```python
# Configure multi-iteration strategy
strategy_config = {
    "iterations": [
        {"base_config": "baseline", "operator": None},
        {"base_config": "enhanced", "operator": "alternative_strategy"}, 
        {"base_config": "enhanced", "operator": "crossover"}
    ]
}

# Run self-evolution process
python SE/basic_run.py --config SE/configs/se_configs/experiment.yaml --mode execute
```

### Custom Operator Development

```python
from SE.operators import TemplateOperator, register_operator

class MyEvolutionOperator(TemplateOperator):
    def _generate_content(self, instance_info, problem_description, trajectory_data):
        # Implement your custom evolution strategy
        return "Your generated strategy content"

# Register and use
register_operator("my_operator", MyEvolutionOperator)
```

### Batch Processing

```bash
# Process multiple SWE-bench instances
sweagent run-batch \
  --config config/default.yaml \
  --agent.model.name deepseek/deepseek-chat \
  --instances.subset verified \
  --instances.slice :10
```

## 🏗️ Architecture Overview

SE-Agent consists of **three main components** working in harmony:

```
📁 SE-Agent Architecture
├── 🧠 SE Framework (SE/)
│   ├── Multi-iteration experiment orchestration
│   ├── Self-evolution operators (Revision, Recombination, Refinement)
│   └── Intelligent trajectory processing & compression
├── 🔧 SWE-Agent Base (sweagent/)  
│   ├── LLM agent implementations
│   ├── Environment interaction layer
│   └── Tool execution system
└── 📊 Trajectory System
    ├── Compressed trajectory storage (.tra files - 80% size reduction)
    ├── Cross-iteration knowledge accumulation
    └── LLM-driven trajectory analysis & summarization
```


## 📦 Installation & Configuration

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone https://github.com/JARVIS-Xs/SE-Agent.git
cd SE-Agent

# 2. Create environment  
conda create -n SE python=3.12
conda activate SE

# 3. Install in editable mode (required)
pip install -e .

# 4. Verify installation
sweagent --help
python SE/test/run_operator_tests.py
```

### Configuration

**Environment Variables:**
```bash
# Create .env file with your API keys
echo "DEEPSEEK_API_KEY=your_deepseek_key" >> .env
echo "OPENAI_API_KEY=your_openai_key" >> .env  
echo "ANTHROPIC_API_KEY=your_anthropic_key" >> .env
```

**SE Configuration Example:**
```yaml
# SE/configs/se_configs/my_experiment.yaml
model:
  name: "deepseek/deepseek-chat"
  api_key: "${DEEPSEEK_API_KEY}"

instances:
  json_file: "SE/instances/test.json"
  key: "instances"

strategy:
  iterations:
    - base_config: "baseconfig1"
      operator: null
    - base_config: "baseconfig2"  
      operator: "alternative_strategy"
    - base_config: "baseconfig2"
      operator: "crossover"

output_dir: "SE/trajectories/my_experiment"
```



## 🧪 Testing & Development

### Running Tests

```bash
# Run all tests
pytest

# Run SE framework tests  
python SE/test/run_operator_tests.py

# Test specific components
python SE/test/test_operators.py
python SE/test/test_traj_pool.py
python SE/test/api_test.py

# Code formatting
ruff check .
ruff format .
```

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-enhancement

# 2. Run tests before changes
python SE/test/run_operator_tests.py

# 3. Make changes and test
python SE/basic_run.py --mode demo  # Quick validation

# 4. Run full test suite
pytest
python SE/test/run_operator_tests.py

# 5. Submit pull request
```

### Creating Custom Operators

SE-Agent's operator system is designed for easy extensibility:

```python
from SE.operators import TemplateOperator, register_operator

class MyCustomOperator(TemplateOperator):
    def get_name(self):
        return "my_custom_operator"
    
    def get_strategy_prefix(self):
        return "MY CUSTOM EVOLUTION STRATEGY"
    
    def _generate_content(self, instance_info, problem_description, trajectory_data):
        # Your custom evolution logic here
        return "Generated evolution strategy content"

# Register the operator
register_operator("my_custom_operator", MyCustomOperator)
```

### Citation

If you use SE-Agent in your research, please cite our paper:

```bibtex
@article{se-agent-2025,
  title={SE-Agent: Self-Evolution Trajectory Optimization in Multi-Step Reasoning with LLM-Based Agents},
  author={Jiaye Lin and Yifu Guo and Yuzhen Han and Sen Hu and Ziyi Ni and Licheng Wang and Mingguang Chen and Daxin Jiang and Binxing Jiao and Chen Hu and Huacan Wang},
  journal={arXiv preprint arXiv:2508.02085},
  year={2025},
  url={https://arxiv.org/abs/2508.02085}
}
```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can get involved:

### Contribution Areas

| Area | Description | Skill Level |
|------|-------------|-------------|
| **🐛 Bug Fixes** | Fix issues in existing code | Beginner |
| **📖 Documentation** | Improve docs and examples | Beginner |
| **🧪 Tests** | Add test cases and improve coverage | Intermediate |
| **🔧 Tools** | Develop utilities and helper scripts | Intermediate |
| **🚀 Features** | Implement new operators and capabilities | Advanced |
| **📊 Research** | Contribute to benchmarking and analysis | Advanced |


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

We would like to thank the following projects and contributors:

- **[SWE-Agent](https://github.com/princeton-nlp/SWE-agent)** - Our foundation framework, developed by Carlos E. Jimenez, John Yang, Kilian Lieret and team
- **[SWE-bench](https://github.com/SWE-bench/SWE-bench)** - For providing the evaluation benchmark and test datasets that enable rigorous assessment of software engineering AI agents
- **[litellm](https://github.com/BerriAI/litellm)** - For unified LLM API interface support
- **Open source community** - For contributions to the advancement of software engineering AI agents

## 📞 Contact & Support

- **📧 Email**: [wanghuacan17@mails.ucas.ac.cn](mailto:wanghuacan17@mails.ucas.ac.cn)
- **🐛 Issues**: [GitHub Issues](https://github.com/JARVIS-Xs/SE-Agent/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/JARVIS-Xs/SE-Agent/discussions)
---

<div align="center">

**⭐ If SE-Agent helps your research or projects, please give us a star! ⭐**

*Made with ❤️ by the SE-Agent Research Team*

</div>
