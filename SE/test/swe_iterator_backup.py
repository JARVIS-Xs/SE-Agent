#!/usr/bin/env python3

"""
Unified SWE-agent batch runner for Aeon framework

This script provides a unified interface for running SWE-agent batch tasks
with configurable parameters loaded from YAML config files.
"""

import json
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from sweagent.run.run_batch import RunBatchConfig, RunBatch
from sweagent.utils.config import load_environment_variables


class UnifiedRunner:
    """Unified runner for SWE-agent batch processing."""
    
    def __init__(self, config_path: str):
        """Initialize the runner with a config file."""
        # Config paths are relative to project root (630_swe)
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        return config
    
    def _validate_and_prepare_paths(self) -> Dict[str, Any]:
        """Validate and prepare file paths from config."""
        config = self.config.copy()
        
        # Resolve JSON file path (relative to project root)
        json_file_path = Path(config['instances']['json_file']).resolve()
            
        if not json_file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
            
        # Validate JSON file content
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = config['instances']['key']
            if key not in data:
                raise KeyError(f"Key '{key}' not found in JSON file")
            instance_ids = data[key]
            if not instance_ids:
                raise ValueError(f"Instance list for key '{key}' is empty")
            print(f"Found {len(instance_ids)} instances for key '{key}'")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file {json_file_path}: {e}")
            
        # Create output directory (relative to project root)
        output_dir = Path(config['output_dir']).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle instance templates directory if specified (optional)
        if 'instance_templates_dir' in config:
            instance_templates_dir = Path(config['instance_templates_dir']).resolve()
            # Only set it if the directory actually exists with templates
            if instance_templates_dir.exists() and any(instance_templates_dir.glob('*.yaml')):
                config['instance_templates_dir'] = str(instance_templates_dir)
                print(f"Using instance templates from: {instance_templates_dir}")
            else:
                # Remove the config to use default system prompt
                config.pop('instance_templates_dir', None)
                print(f"Instance templates directory {instance_templates_dir} not found or empty, using default system prompt")
            
        # Update paths to absolute paths
        config['instances']['path'] = str(json_file_path)
        config['output_dir'] = str(output_dir)
        
        return config
    
    def _merge_base_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge with base configuration file if specified."""
        if 'base_config' not in config:
            return config
            
        base_config_path = Path(config['base_config'])
        if not base_config_path.exists():
            print(f"Warning: Base config file not found: {base_config_path}")
            return config
            
        with open(base_config_path, 'r', encoding='utf-8') as f:
            base_config = yaml.safe_load(f)
            
        # Merge configs with current config taking precedence
        merged_config = base_config.copy()
        for key, value in config.items():
            if key == 'base_config':
                continue
            if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                merged_config[key].update(value)
            else:
                merged_config[key] = value
                
        return merged_config
    
    def _build_run_config(self) -> Dict[str, Any]:
        """Build the final configuration for RunBatch."""
        config = self._validate_and_prepare_paths()
        config = self._merge_base_config(config)
        
        # Start with the merged config and override specific fields
        run_config = config.copy()
        
        # Override model configuration with our specific values
        if 'agent' not in run_config:
            run_config['agent'] = {}
        if 'model' not in run_config['agent']:
            run_config['agent']['model'] = {}
            
        # Update model configuration with our values
        run_config['agent']['model'].update({
            'name': config['model']['name'],
            'api_base': config['model'].get('api_base'),
            'api_key': config['model'].get('api_key', 'empty'),
            'max_input_tokens': config['model'].get('max_input_tokens', 128000),
            'max_output_tokens': config['model'].get('max_output_tokens', 64000),
            'per_instance_cost_limit': config['model'].get('per_instance_cost_limit', 0),
            'total_cost_limit': config['model'].get('total_cost_limit', 0),
        })
        
        # Override instances configuration
        run_config['instances'] = {
            'type': 'id_list',
            'path': config['instances']['path'],
            'key': config['instances']['key'],
            'subset': config['instances'].get('subset', 'verified'),
            'split': config['instances'].get('split', 'test'),
            'shuffle': config['instances'].get('shuffle', False),
            'evaluate': config['instances'].get('evaluate', False)
        }
        
        # Add deployment config from base config if it exists
        if 'instances' in config and isinstance(config['instances'], dict) and 'deployment' in config['instances']:
            run_config['instances']['deployment'] = config['instances']['deployment']
        
        # Override output configuration
        run_config['output_dir'] = config['output_dir']
        run_config['suffix'] = config.get('suffix', 'unified_run')
        run_config['num_workers'] = config.get('num_workers', 4)
        
        # Add instance templates directory if specified
        if 'instance_templates_dir' in config:
            run_config['instance_templates_dir'] = config['instance_templates_dir']
            
        # Remove the temporary model section from the top level
        if 'model' in run_config:
            del run_config['model']
            
        return run_config
    
    def run(self) -> None:
        """Execute the batch run."""
        run_config = self._build_run_config()
        
        # Print config (hide API key)
        print_config = json.loads(json.dumps(run_config))
        if 'agent' in print_config and 'model' in print_config['agent'] and 'api_key' in print_config['agent']['model']:
            print_config['agent']['model']['api_key'] = '********'
        print(f"Run configuration: {json.dumps(print_config, indent=2, ensure_ascii=False)}")
        
        # Load environment variables
        print("Loading environment variables...")
        load_environment_variables()
        
        try:
            print("Creating RunBatchConfig instance...")
            config = RunBatchConfig.model_validate(run_config)
            print("Creating RunBatch instance...")
            run_batch = RunBatch.from_config(config)
            print("Starting batch processing...")
                
            run_batch.main()
            
            print(f"Completed! Results saved to {run_config['output_dir']}")
            if 'instance_templates_dir' in run_config:
                print(f"Instance templates directory: {run_config['instance_templates_dir']}")
                
        except Exception as e:
            print(f"Batch processing failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Unified SWE-agent batch runner')
    parser.add_argument('config', nargs='?', default="Aeon/run/configs/test_claude.yaml", help='Path to configuration YAML file')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate configuration without running')
    
    args = parser.parse_args()
    
    try:
        runner = UnifiedRunner(args.config)
        if args.validate_only:
            runner._build_run_config()
            print("Configuration validation successful!")
        else:
            runner.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()