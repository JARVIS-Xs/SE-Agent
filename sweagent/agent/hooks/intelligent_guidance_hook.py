"""
Intelligent Guidance Hook - Adapted from existing working implementation

Provides intelligent prompt injection when agents encounter errors.
Automatically injects alternative solution guidance based on pre-analyzed data.
"""

import copy
import datetime
import logging
from typing import Any, Dict, List

from sweagent.agent.hooks.abstract import AbstractAgentHook
from sweagent.types import Trajectory
from sweagent.utils.log import get_logger


class IntelligentGuidanceHook(AbstractAgentHook):
    """Hook that provides intelligent guidance when agents encounter errors.
    
    This hook monitors agent execution for error conditions and automatically
    injects alternative solution guidance based on analysis of previous attempts.
    """
    
    # Shared class variable for enhancement data (thread-safe through GIL)
    enhance_history_dict = None
    
    def __init__(self):
        """Initialize the intelligent guidance hook."""
        self.logger = get_logger("intelligent-guidance", emoji="🧠")
        
    def revise_history_before_query(self, *, messages: list[dict[str, str]], trajectory: Trajectory, instance_id: str) -> list[dict[str, str]]:
        """Revise conversation history to inject intelligent guidance when errors are detected.
        
        Args:
            messages: Current conversation history
            trajectory: Current trajectory
            instance_id: Instance identifier
            
        Returns:
            Modified conversation history with guidance injected if appropriate
        """
        if not messages:
            return messages
            
        # Deep copy to avoid modifying original
        messages_copy = copy.deepcopy(messages)
        
        # Get the latest message
        latest_msg = messages_copy[-1]
        
        if latest_msg.get("role") == "tool":
            # Check if latest message is a tool response, analyze for errors
            content = latest_msg.get("content", "")
            action = messages_copy[-2].get("action", "") if len(messages_copy) >= 2 else ""
            
            # Extract debug filename from create commands
            debug_filename = self._extract_reproduce_filename_from_create(messages_copy)
            
            # Error detection logic (adapted from your working implementation)
            if "Traceback" in content or (debug_filename and debug_filename in action):
                self.logger.info(f"Error detected in {instance_id}, checking for guidance data...")
                
                # Check if enhancement data is available
                if self.enhance_history_dict is None:
                    self.logger.info("enhance_history_dict is None, skipping guidance injection")
                    return messages_copy
                
                # Check if instance exists in enhancement data
                if instance_id not in self.enhance_history_dict:
                    self.logger.info(f"{instance_id} not found in enhance_history_dict, skipping guidance injection")
                    return messages_copy
                
                # Check if claude_analysis exists
                if "claude_analysis" not in self.enhance_history_dict[instance_id]:
                    self.logger.info(f"claude_analysis not found for {instance_id}, skipping guidance injection")
                    return messages_copy
                
                # Check if already called (one-time injection mechanism)
                analysis_data = self.enhance_history_dict[instance_id]["claude_analysis"]
                is_called = analysis_data.get("is_called")
                
                if is_called:
                    self.logger.info(f"Guidance already provided for {instance_id}, skipping")
                    return messages_copy
                
                # Generate and inject guidance prompt
                guidance_prompt = self._generate_guidance_prompt(analysis_data)
                
                if guidance_prompt:
                    # Inject the guidance message
                    messages_copy.append({
                        "role": "user",
                        "content": guidance_prompt,
                        "message_type": "guidance"
                    })
                    
                    # Mark as called to prevent future injections
                    self.enhance_history_dict[instance_id]["claude_analysis"]["is_called"] = datetime.datetime.now().isoformat()
                    
                    self.logger.info(f"Intelligent guidance injected for {instance_id}")
                else:
                    # Fallback generic guidance
                    messages_copy.append({
                        "role": "user", 
                        "content": "Excellent, you have successfully reproduced the bug.\n\nNow, go beyond the immediate error and perform a deeper analysis",
                        "message_type": "guidance"
                    })
                    
                    self.enhance_history_dict[instance_id]["claude_analysis"]["is_called"] = datetime.datetime.now().isoformat()
                    self.logger.info(f"Generic guidance injected for {instance_id}")
        
        return messages_copy
    
    def _extract_reproduce_filename_from_create(self, messages: List[Dict[str, Any]]) -> str:
        """Extract debug filename from create commands (adapted from working implementation).
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Debug filename if found, empty string otherwise
        """
        # Look for 'create' commands starting from message 27 (as in original)
        for msg in messages[27:]:
            action = msg.get("action", "")
            if "create" in action:
                return action.replace("create", "python", 1)
        return ""
    
    def _generate_guidance_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate intelligent guidance prompt based on analysis data.
        
        Args:
            analysis_data: Claude analysis data from enhancement JSON
            
        Returns:
            Generated guidance prompt
        """
        if not analysis_data:
            return ""
        
        # Extract analysis fields (exactly as in your working implementation)
        approach_summary = analysis_data.get("approach_summary", "uncertain approach")
        modified_files = analysis_data.get("modified_files", "unknown files")
        key_changes = analysis_data.get("key_changes", "unspecified changes")
        strategy = analysis_data.get("strategy", "unknown strategy")
        specific_technique = analysis_data.get("specific_technique_from_first_solution", "unspecified technique")
        specific_files = analysis_data.get("specific_files_or_functions", "unknown files")
        assumptions = analysis_data.get("assumptions_made_in_first_solution", "unspecified assumptions")
        different_perspective = analysis_data.get("different_perspective", "alternative approach")
        component_not_touched = analysis_data.get("component_not_touched_in_first_solution", "unexplored components")
        
        # Generate the detailed guidance prompt (your exact template)
        prompt = f"""
Excellent, you have successfully reproduced the bug. Now, let's develop a different approach to fix it.
I've analyzed the first solution attempt, and here's what I found:
The first solution approached this problem by {approach_summary}. It modified {modified_files}, and the key changes involved {key_changes}.
The core strategy used was "{strategy}" which may have limitations. Specifically, the solution used {specific_technique} and focused on changing {specific_files}.
This approach makes some assumptions: {assumptions}
For our alternative solution, I want you to explore a completely different approach. Instead of following the same strategy, consider looking at this from a "{different_perspective}" angle.
You might want to investigate {component_not_touched} as a potential area for your solution.

Remember, your goal is to create a patch that:
1. Solves the same problem but uses a fundamentally different approach
2. Avoids the techniques used in the first solution
3. Challenges the assumptions made in the first solution
4. Still aims to generate a patch that passes all tests, and use the 'submit' command when you believe your modifications are complete

Please analyze the problem again from this new perspective and develop your alternative solution.
"""
        return prompt


def create_intelligent_guidance_hook() -> IntelligentGuidanceHook:
    """Factory function to create an intelligent guidance hook.
    
    Returns:
        Configured IntelligentGuidanceHook instance
    """
    return IntelligentGuidanceHook()


def load_enhancement_data(json_file_path: str) -> bool:
    """Load enhancement data from JSON file into the hook's shared storage.
    
    Args:
        json_file_path: Path to the enhancement JSON file
        
    Returns:
        True if loaded successfully, False otherwise
    """
    import json
    from pathlib import Path
    
    logger = get_logger("enhancement-loader", emoji="📊")
    
    try:
        json_path = Path(json_file_path)
        if not json_path.exists():
            logger.error(f"Enhancement data file not found: {json_file_path}")
            return False
            
        # Only load if not already loaded (prevent duplicate loading)
        if IntelligentGuidanceHook.enhance_history_dict is None:
            logger.info(f"Loading enhancement data from: {json_file_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                IntelligentGuidanceHook.enhance_history_dict = json.load(f)
            logger.info(f"Successfully loaded enhancement data for {len(IntelligentGuidanceHook.enhance_history_dict)} instances")
        else:
            logger.info("Enhancement data already loaded, skipping")
            
        return True
        
    except Exception as e:
        logger.error(f"Error loading enhancement data: {e}")
        return False