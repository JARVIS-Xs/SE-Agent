#!/usr/bin/env python3

"""
System prompt creation tool for generating alternative solution strategies

This script creates a new numbered folder and generates alternative system prompts
that provide completely different approaches to solving the same problems, helping
agents avoid repeating failed strategies.
"""

import yaml
import json
import argparse
import re
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from utils.llm_integration to reuse implementation
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from llm_integration import load_config_from_yaml
from sweagent.agent.models import get_model, GenericAPIModelConfig
from sweagent.tools.tools import ToolConfig


class SystemPromptCreator:
    """Creates alternative system prompts for failed trajectory instances."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        # Config paths are relative to project root (630_swe)
        self.config_path = Path(config_path)
        
        # Load config for output_dir etc
        self.config = yaml.safe_load(self.config_path.read_text())
        self.model = None  # Will store the model instance
        
    def _find_newest_numbered_folder(self) -> int:
        """Find the newest numbered folder in the project root."""
        project_root = Path(__file__).parent
        
        # Find all numbered folders (matching pattern like 20250612_trae, 24_6_success_fix20_first_try etc.)
        numbered_folders = []
        for item in project_root.iterdir():
            if item.is_dir():
                # Extract leading number from folder name
                match = re.match(r'^(\d+)', item.name)
                if match:
                    numbered_folders.append(int(match.group(1)))
        
        if not numbered_folders:
            return 0  # Start from 1 if no numbered folders exist
        
        return max(numbered_folders)
    
    def _create_new_folder_structure(self) -> Path:
        """Create new numbered folder in output_dir/system_prompt/{num}."""
        output_dir_config = self.config['output_dir']
        
        # Output dir is relative to project root
        output_dir = Path(output_dir_config).resolve()
        
        # Find the highest numbered directory in output_dir/system_prompt/
        system_prompt_base = output_dir / "system_prompt"
        newest_number = 0
        
        if system_prompt_base.exists():
            for item in system_prompt_base.iterdir():
                if item.is_dir() and item.name.isdigit():
                    numbered_dirs = [int(item.name)]
                    if numbered_dirs:
                        newest_number = max(newest_number, max(numbered_dirs))
        
        # Create new numbered folder (minimum 2 per workflow logic)
        new_number = max(newest_number + 1, 2)
        system_prompts_dir = system_prompt_base / str(new_number)
        system_prompts_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Created new folder structure: {system_prompts_dir}")
        return system_prompts_dir
    
    def _get_trajectory_files(self) -> List[Tuple[Path, Path, int]]:
        """Discover trajectory files in the output directory. Returns (instance_dir, trajectory_file, run_number)."""
        output_dir_config = self.config['output_dir']
        
        # Output dir is relative to project root
        output_dir = Path(output_dir_config).resolve()
        
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
        
        trajectory_files = []
        
        # Find all instance directories
        for instance_dir in output_dir.iterdir():
            if not instance_dir.is_dir() or instance_dir.name.startswith('.'):
                continue
                
            # Find the highest numbered subdirectory (e.g., if 1,2,3 exist, use 3)
            run_dirs = [d for d in instance_dir.iterdir() 
                       if d.is_dir() and d.name.isdigit()]
            
            if not run_dirs:
                continue
                
            # Get the highest numbered run directory
            highest_run = max(run_dirs, key=lambda d: int(d.name))
            run_number = int(highest_run.name)
            
            # Find .tra files only in the highest run directory
            for file_path in highest_run.iterdir():
                if file_path.suffix == '.tra':
                    trajectory_files.append((instance_dir, file_path, run_number))
        
        return trajectory_files
    
    def _load_trajectory_data(self, trajectory_file: Path) -> Dict[str, Any]:
        """Load trajectory data from .tra file."""
        try:
            with open(trajectory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading trajectory file {trajectory_file}: {e}")
            return {}
    
    def _load_traj_pool(self, instance_dir: Path) -> Dict[str, str]:
        """Load traj.pool file from instance directory."""
        traj_pool_file = instance_dir / "traj.pool"
        
        if not traj_pool_file.exists():
            print(f"Warning: traj.pool not found in {instance_dir}")
            return {}
        
        try:
            with open(traj_pool_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading traj.pool from {instance_dir}: {e}")
            return {}
    
    def _extract_problem_statement(self, trajectory_data: Dict[str, Any]) -> str:
        """Extract problem statement from trajectory data."""
        try:
            # Get the second item (first user message) from Trajectory
            trajectory = trajectory_data.get('Trajectory', [])
            if len(trajectory) >= 2:
                user_item = trajectory[1]  # Second item (index 1)
                if user_item.get('role') == 'user' and 'content' in user_item:
                    content = user_item['content']
                    # Extract text from pr_description tags
                    if isinstance(content, list) and len(content) > 0:
                        text = content[0].get('text', '')
                    elif isinstance(content, str):
                        text = content
                    else:
                        return ""
                    
                    # Extract content between <pr_description> tags
                    match = re.search(r'<pr_description>\s*(.*?)\s*</pr_description>', text, re.DOTALL)
                    if match:
                        return match.group(1).strip()
            return ""
        except Exception as e:
            print(f"Error extracting problem statement: {e}")
            return ""
    
    def _call_llm_api(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM API with the given prompt using sweagent model infrastructure."""
        # Load model config but ignore cost limits (those are for runner only)
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        model_config_data = config.get('model', {})
        
        # Create model config without restrictive cost limits
        model_config = GenericAPIModelConfig(
            name=model_config_data.get('name', 'anthropic/claude-sonnet-4-20250514'),
            api_base=model_config_data.get('api_base'),
            api_key=model_config_data.get('api_key'),
            max_input_tokens=model_config_data.get('max_input_tokens'),
            max_output_tokens=model_config_data.get('max_output_tokens'),
            # Generators need no cost limits (0 = unlimited)
            per_instance_cost_limit=0,
            total_cost_limit=0,
            temperature=model_config_data.get('temperature', 0.0),
            top_p=model_config_data.get('top_p', 1.0),
        )
        
        # Create minimal tool config (required for model initialization) - disable function calling
        tools = ToolConfig(
            commands=[],
            use_function_calling=False,
            submit_command="submit"
        )
        
        # Initialize model if needed
        if self.model is None:
            self.model = get_model(model_config, tools)
        
        # Create message history
        history = []
        if system_prompt:
            history.append({"role": "system", "content": system_prompt})
        history.append({"role": "user", "content": prompt})
        
        try:
            # Query the model using the same approach as test_llm_integration.py
            response = self.model.query(history)
            message = response.get("message", "")
            if message:
                return message
            else:
                print("No message in response, returning empty string")
                return ""
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return ""
    
    def _generate_alternative_strategy(self, problem_statement: str, previous_approach: str, instance_name: str) -> str:
            """Generate a completely different solution strategy using LLM."""
            system_prompt = """You are an expert software engineering strategy consultant specializing in innovative problem-solving. Your task is to generate radically divergent problem-solving approaches for software engineering tasks, drawing from diverse methodologies across fields like reverse engineering, data-driven analysis, simulation-based testing, or interdisciplinary techniques borrowed from domains such as systems biology or game theory.

    You will be given a problem and a previous approach that FAILED. Your job is to create a fundamentally orthogonal strategy that:
    1. Leverages entirely novel investigation paradigms, such as starting from end-user impact analysis or component isolation experiments
    2. Approaches the problem from an unconventional angle, like focusing on runtime behavior tracing instead of static code review
    3. Incorporates alternative tools, techniques, or conceptual frameworks, such as visualization tools for data flow or probabilistic modeling for error prediction
    4. Establishes a distinct logical progression, perhaps iterative prototyping over linear debugging

    CRITICAL: Your strategy must be architecturally dissimilar to evade the inherent limitations and blind spots of the prior attempt, ensuring it probes unexplored dimensions of the problem space.

    Respond with a high-level conceptual strategy that outlines key actionable steps. Emphasize the COGNITIVE FRAMEWORK rather than granular code specifics.

    IMPORTANT: 
    - Respond ONLY with plain text without markdown formatting
    - Do NOT use bullet points, headers, or special formatting
    - Do NOT use any tools, commands, or function calls
    - Provide ONLY the text content of the strategy
    - Your response should be a cohesive strategic narrative in paragraph form"""
            
            prompt = f"""Generate a radically divergent solution strategy for this software engineering problem:

    PROBLEM:
    {problem_statement}

    PREVIOUS FAILED APPROACH:
    {previous_approach}

    Requirements for the alternative strategy:
    1. Adopt a profoundly different investigation paradigm, such as empirical experimentation or holistic system modeling
    2. Initiate from an alternative entry point (e.g., examining dependencies externally or simulating environmental factors)
    3. Pursue a non-linear or inverted logical sequence, like working backwards from symptoms to causes
    4. Integrate unconventional debugging/analysis techniques, such as fuzzing, profiling, or comparative benchmarking
    5. Prioritize overlooked aspects, like performance metrics, edge-case simulations, or cross-version diffs
    6. Incorporate diverse tools and commands, potentially from outside the standard toolkit, where feasible

    The strategy should be conceptual yet executable - articulate the reasoning paradigm and pivotal strategic phases that would enable an agent to tackle this problem via an entirely novel trajectory.

    Elaborate on WHY this approach diverges significantly and HOW it circumvents the shortcomings of the previous effort, potentially by introducing variability in assumptions or exploring parallel hypotheses.

    Craft a strategy that empowers an AI agent to reconceptualize the problem from ground zero with an innovative methodology, fostering breakthrough potential."""
            
            return self._call_llm_api(prompt, system_prompt)
    
    def _create_yaml_content(self, alternative_strategy: str) -> str:
        """Create YAML content with the required format."""
        # Required prefix
        prefix = "You are a helpful assistant that can interact with a terminal to solve software engineering tasks."
        
        # Combine prefix with the alternative strategy
        full_content = f"{prefix}\n\nALTERNATIVE SOLUTION STRATEGY:\n\n{alternative_strategy}"
        
        # Create YAML structure matching the reference format
        yaml_content = {
            'agent': {
                'templates': {
                    'system_template': full_content
                }
            }
        }
        
        return yaml.dump(yaml_content, default_flow_style=False, allow_unicode=True, width=1000)
    
    def _save_yaml_file(self, instance_name: str, yaml_content: str, output_dir: Path) -> None:
        """Save YAML file for the instance."""
        output_file = output_dir / f"{instance_name}.yaml"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"Saved alternative strategy to: {output_file}")
    
    def create_system_prompts(self) -> None:
        """Main method to create alternative system prompts."""
        print(f"Starting system prompt creation with config: {self.config_path}")
        
        # Create new folder structure
        output_dir = self._create_new_folder_structure()
        
        # Get trajectory files
        trajectory_files = self._get_trajectory_files()
        if not trajectory_files:
            print("No trajectory files found")
            return
        
        print(f"Found {len(trajectory_files)} trajectory files")
        
        processed_count = 0
        
        # Process each trajectory file
        for instance_dir, trajectory_file, run_number in trajectory_files:
            try:
                instance_name = instance_dir.name
                print(f"Processing instance: {instance_name}")
                
                # Load trajectory data to extract problem statement
                trajectory_data = self._load_trajectory_data(trajectory_file)
                if not trajectory_data:
                    print(f"Skipping {instance_name}: Could not load trajectory data")
                    continue
                
                # Extract problem statement
                problem_statement = self._extract_problem_statement(trajectory_data)
                if not problem_statement:
                    print(f"Skipping {instance_name}: Could not extract problem statement")
                    continue
                
                # Load traj.pool to get previous approach
                traj_pool = self._load_traj_pool(instance_dir)
                if not traj_pool:
                    print(f"Skipping {instance_name}: Could not load traj.pool")
                    continue
                
                # Get the trajectory conclusion for this run number
                previous_approach = traj_pool.get(str(run_number), "")
                if not previous_approach:
                    print(f"Skipping {instance_name}: No trajectory conclusion found for run {run_number}")
                    continue
                
                # Generate alternative strategy
                print(f"Generating alternative strategy for {instance_name}...")
                alternative_strategy = self._generate_alternative_strategy(
                    problem_statement, previous_approach, instance_name
                )
                
                if not alternative_strategy:
                    print(f"Failed to generate strategy for {instance_name}")
                    continue
                
                # Create and save YAML content
                yaml_content = self._create_yaml_content(alternative_strategy)
                self._save_yaml_file(instance_name, yaml_content, output_dir)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {instance_name}: {e}")
                continue
        
        print(f"Successfully processed {processed_count} instances")
        print(f"Alternative system prompts saved to: {output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Create alternative system prompts for failed trajectories')
    parser.add_argument('config', nargs='?', default="Aeon/configs/test_claude.yaml", 
                       help='Path to configuration YAML file')
    
    args = parser.parse_args()
    
    try:
        creator = SystemPromptCreator(args.config)
        creator.create_system_prompts()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()