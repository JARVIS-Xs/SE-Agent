#!/usr/bin/env python3

"""
Trajectory reorganization tool for Aeon framework

This script reorganizes trajectory files from trajectory/instance_id/(items) 
to trajectory/instance_id/1/(items) based on the config file structure.
Enhanced with iterative organization and .tra file generation.
"""

import yaml
import shutil
import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any, List


class TrajectoryReorganizer:
    """Reorganizes trajectory files based on config."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        return config
    
    def _get_next_run_number(self, instance_dir: Path) -> int:
        """Get the next available run number for iterative organization."""
        existing_runs = [int(d.name) for d in instance_dir.iterdir() 
                        if d.is_dir() and d.name.isdigit()]
        return max(existing_runs) + 1 if existing_runs else 1
    
    def _count_tokens(self, text: str) -> int:
        """Simple token counting approximation."""
        # Basic token counting - split by whitespace and common punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        return len(tokens)
    
    def _truncate_tool_content(self, content):
        """Truncate tool content using character-based approach with percentage constraints."""
        if not content:
            return content
            
        # Handle list format: [{"type": "text", "text": "..."}]
        if isinstance(content, list) and len(content) > 0:
            # Extract the first text item and truncate it
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                text_content = first_item["text"]
                if isinstance(text_content, str):
                    truncated_text = self._truncate_text(text_content)
                    # Return simplified format with just the truncated text
                    return truncated_text
        
        # Handle string format directly
        if isinstance(content, str):
            return self._truncate_text(content)
        
        return content
    
    def _truncate_text(self, text: str, first_percent: float = 0.2, last_percent: float = 0.1) -> str:
        """Truncate text content using character-based approach with percentage constraints."""
        if not text or not isinstance(text, str):
            return text
            
        text_length = len(text)
        
        # Only truncate if text is long enough to benefit from truncation
        if text_length < 300:  # Don't truncate short content
            return text
        
        # Calculate first part length (20% of content, constrained between 30-150 chars)
        first_length = int(text_length * first_percent)
        first_length = max(30, min(150, first_length))
        
        # Calculate last part length (10% of content, constrained between 30-100 chars)  
        last_length = int(text_length * last_percent)
        last_length = max(30, min(100, last_length))
        
        # Check if truncation would actually save space
        truncated_length = first_length + last_length + len("... [TRUNCATED] ...")
        if truncated_length >= text_length * 0.8:  # If we're keeping more than 80%, don't truncate
            return text
            
        # Extract first and last parts
        first_part = text[:first_length]
        last_part = text[-last_length:]
        
        # Combine with truncation marker
        return f"{first_part}... [TRUNCATED] ...{last_part}"
    
    def _create_tra_file(self, traj_file: Path, tra_file: Path) -> Dict[str, int]:
        """Create .tra file from .traj file with only history role/content."""
        try:
            with open(traj_file, 'r', encoding='utf-8') as f:
                traj_data = json.load(f)
            
            # Extract history with only role and content
            history = traj_data.get('history', [])
            simplified_history = []
            total_tokens = 0
            
            for item in history:
                if 'role' in item:
                    simplified_item = {
                        'role': item['role']
                    }
                    
                    # Handle different roles differently
                    if item['role'] == 'assistant':
                        # Extract thought instead of content for assistant roles
                        if 'thought' in item and item['thought']:
                            simplified_item['thought'] = item['thought']
                        
                        # Include action for assistant roles
                        if 'action' in item and item['action']:
                            action = item['action']
                            
                            # Apply truncation for str_replace_editor or very long actions (>350 chars)
                            if isinstance(action, str):
                                if 'str_replace_editor' in action or len(action) > 350:
                                    action = self._truncate_text(action)
                            elif isinstance(action, dict):
                                # Handle action dict format if needed
                                action_str = str(action)
                                if 'str_replace_editor' in action_str or len(action_str) > 350:
                                    action = self._truncate_text(action_str)
                            
                            simplified_item['action'] = action
                            
                    else:
                        # For non-assistant roles, use content
                        if 'content' in item and item['content']:
                            content = item['content']
                            
                            # Apply truncation for tool roles with long observations
                            if item['role'] == 'tool':
                                content = self._truncate_tool_content(content)
                            
                            simplified_item['content'] = content
                    
                    # Only add item if it has meaningful content (not just role)
                    if len(simplified_item) > 1:
                        simplified_history.append(simplified_item)
                        
                        # Count tokens for all fields
                        for field in ['content', 'thought', 'action']:
                            if field in simplified_item:
                                field_str = str(simplified_item[field]) if simplified_item[field] else ""
                                total_tokens += self._count_tokens(field_str)
            
            # Create .tra file content
            tra_data = {
                'Trajectory': simplified_history
            }
            
            # Write .tra file
            with open(tra_file, 'w', encoding='utf-8') as f:
                json.dump(tra_data, f, indent=2)
            
            return {
                'total_tokens': total_tokens,
                'history_items': len(simplified_history)
            }
            
        except Exception as e:
            print(f"Error creating .tra file for {traj_file}: {e}")
            return {'total_tokens': 0, 'history_items': 0}
    
    def reorganize(self) -> None:
        """Reorganize trajectory files with iterative organization."""
        output_dir = Path(self.config['output_dir']).resolve()
        
        if not output_dir.exists():
            print(f"Output directory not found: {output_dir}")
            return
            
        print(f"Reorganizing trajectories in: {output_dir}")
        
        # Find all instance directories
        instance_dirs = [d for d in output_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        log_data = []
        
        for instance_dir in instance_dirs:
            # Find files that need to be organized (exclude traj.pool)
            files_to_organize = [f for f in instance_dir.iterdir() 
                               if f.is_file() and f.name != "traj.pool"]
            
            if not files_to_organize:
                print(f"No files to organize in {instance_dir.name}")
                continue
            
            # Get next run number for iterative organization
            run_number = self._get_next_run_number(instance_dir)
            new_subdir = instance_dir / str(run_number)
            new_subdir.mkdir(exist_ok=True)
            
            # Move files and process .traj files
            files_moved = 0
            for file_path in files_to_organize:
                target_path = new_subdir / file_path.name
                shutil.move(str(file_path), str(target_path))
                files_moved += 1
                
                # Process .traj files to create .tra files
                if file_path.suffix == '.traj':
                    tra_file = new_subdir / (file_path.stem + '.tra')
                    stats = self._create_tra_file(target_path, tra_file)
                    
                    log_entry = {
                        'instance_id': instance_dir.name,
                        'run_number': run_number,
                        'traj_file': file_path.name,
                        'tra_file': tra_file.name,
                        'total_tokens': stats['total_tokens'],
                        'history_items': stats['history_items']
                    }
                    log_data.append(log_entry)
                    
                    print(f"Created {tra_file.name} with {stats['history_items']} history items, "
                          f"~{stats['total_tokens']} tokens")
            
            print(f"Organized {instance_dir.name}: moved {files_moved} files to run {run_number}")
        
        # Write log file
        log_file = output_dir / 'trajectory_processing_log.json'
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"Processing complete! Log saved to {log_file}")
        
        # Print summary
        total_tokens = sum(entry['total_tokens'] for entry in log_data)
        total_files = len(log_data)
        print(f"\nSummary: Processed {total_files} trajectory files, "
              f"~{total_tokens} total tokens")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Reorganize trajectory files')
    parser.add_argument('config', nargs='?', default="Aeon/run/configs/test_claude.yaml", 
                       help='Path to configuration YAML file')
    
    args = parser.parse_args()
    
    try:
        reorganizer = TrajectoryReorganizer(args.config)
        reorganizer.reorganize()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()