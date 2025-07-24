#!/usr/bin/env python3

"""
Trajectory pool extraction tool for analyzing all strategy approaches

This script analyzes ALL strategy approaches stored in traj.pool files to generate
comprehensive system prompts that synthesize insights from multiple attempts at 
solving the same problem.
"""

import yaml
import json
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from utils.llm_integration to reuse implementation
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from llm_integration import load_config_from_yaml
from sweagent.agent.models import get_model, GenericAPIModelConfig
from sweagent.tools.tools import ToolConfig


class TrajPoolExtractor:
    """Extracts and analyzes all strategy approaches from traj.pool files."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        # Config paths are relative to project root (630_swe)
        self.config_path = Path(config_path)
        
        # Load config for output_dir etc
        self.config = yaml.safe_load(self.config_path.read_text())
        self.model = None  # Will store the model instance
        
    def _create_new_folder_structure(self) -> Path:
        """Create new numbered folder in output_dir/system_prompt/{num} for next run."""
        output_dir_config = self.config['output_dir']
        
        # Output dir is relative to project root
        output_dir = Path(output_dir_config).resolve()
        
        # Find the highest numbered directory in output_dir/system_prompt/
        system_prompt_base = output_dir / "system_prompt"
        newest_number = 0
        
        if system_prompt_base.exists():
            for item in system_prompt_base.iterdir():
                if item.is_dir() and item.name.isdigit():
                    newest_number = max(newest_number, int(item.name))
        
        # Create new numbered folder for next run (minimum 2 per workflow logic)
        new_number = max(newest_number + 1, 2)
        system_prompts_dir = system_prompt_base / str(new_number)
        system_prompts_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Created system_prompt folder for next run: {system_prompts_dir}")
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
        """Load ALL strategy approaches from traj.pool file."""
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
    
    def _analyze_all_approaches(self, problem_statement: str, all_approaches: Dict[str, str]) -> str:
        """Generate a radically different, actionable strategy based on all previous approaches."""
        system_prompt = """You are an expert software engineering strategist specializing in innovative reinvention. Your task is to synthesize insights from multiple solution approaches for the same problem and directly generate a radically different problem-solving strategy that provides clear, actionable instructions on how to approach the issue in a new way.\n\nYou will be given a problem and ALL attempted approaches. Your job is to:\n1. Use the collective insights from the approaches as implicit inspiration without explicit analysis\n2. Design an entirely novel strategy that diverges in methodology, tools, and logic\n3. Focus the output exclusively on a step-by-step actionable guide for executing this new strategy\n4. Ensure the guide includes specific actions, decision points, and tools to facilitate direct implementation\n\nEmphasize forward-looking, practical steps that reframe the problem-solving process for breakthrough results.\n\nIMPORTANT: \n- Respond ONLY with plain text without markdown formatting\n- Do NOT use bullet points, headers, or special formatting\n- Do NOT use any tools, commands, or function calls\n- Provide ONLY the text content of the strategy\n- Your response should be a detailed, paragraph-form execution guide for the new strategy"""
        
        # Format all approaches for the prompt
        approaches_text = ""
        for run_num, approach in all_approaches.items():
            approaches_text += f"\nAPPROACH {run_num}:\n{approach}\n"
        
        prompt = f"""Based on the problem and all attempted approaches provided, generate a completely divergent strategy with explicit, step-by-step instructions on how to execute it:

        PROBLEM:
        {problem_statement}

        ALL ATTEMPTED APPROACHES:
        {approaches_text}

        In your response, focus solely on:
        1. The conceptual foundation of the new strategy and its key divergences
        2. A sequential guide on how to implement it, detailing specific actions, decision points, and checkpoints
        3. Rationale for why this approach enables success through its unique structure
        4. Tips for adapting this strategy to similar problems in the future

        Center on fueling innovation through a blueprint for breakthrough approaches that transcend the given attempts. Ensure the proposed scheme introduces novel elements like alternative tools, inverted logic, or interdisciplinary inspirations to guarantee differentiation. This output is intended to serve as a concise system prompt for another AI agent, so keep it strategic, focused, and under 600 words to maintain effectiveness.
        """        
        return self._call_llm_api(prompt, system_prompt)
    
    def _create_yaml_content(self, comprehensive_analysis: str) -> str:
        """Create YAML content with the required format."""
        # Required prefix
        prefix = "You are a helpful assistant that can interact with a terminal to solve software engineering tasks."
        
        # Combine prefix with the comprehensive analysis
        full_content = f"{prefix}\n\nCOMPREHENSIVE STRATEGY ANALYSIS:\n\n{comprehensive_analysis}"
        
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
        
        print(f"Saved comprehensive analysis to: {output_file}")
    
    def extract_pool_insights(self) -> None:
        """Main method to extract insights from all traj.pool approaches."""
        print(f"Starting traj.pool analysis with config: {self.config_path}")
        
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
                
                # Load ALL approaches from traj.pool
                all_approaches = self._load_traj_pool(instance_dir)
                if not all_approaches:
                    print(f"Skipping {instance_name}: Could not load traj.pool or it's empty")
                    continue
                
                print(f"Found {len(all_approaches)} approaches in traj.pool for {instance_name}")
                
                # Analyze all approaches comprehensively
                print(f"Analyzing all approaches for {instance_name}...")
                comprehensive_analysis = self._analyze_all_approaches(
                    problem_statement, all_approaches
                )
                
                if not comprehensive_analysis:
                    print(f"Failed to generate analysis for {instance_name}")
                    continue
                
                # Create and save YAML content
                yaml_content = self._create_yaml_content(comprehensive_analysis)
                self._save_yaml_file(instance_name, yaml_content, output_dir)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {instance_name}: {e}")
                continue
        
        print(f"Successfully processed {processed_count} instances")
        print(f"System prompts for next run saved to: {output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Extract comprehensive insights from all traj.pool approaches')
    parser.add_argument('config', nargs='?', default="Aeon/configs/test_claude.yaml", 
                       help='Path to configuration YAML file')
    
    args = parser.parse_args()
    
    try:
        extractor = TrajPoolExtractor(args.config)
        extractor.extract_pool_insights()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()