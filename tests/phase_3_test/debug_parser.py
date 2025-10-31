#!/usr/bin/env python3

import json
import logging
import sys
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("debug")

# Add the project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import the parsing function
from core.utils.parsers.agent_parser import parse_agents_from_phase2, extract_xml_content, clean_and_fix_xml, extract_agent_fallback

def print_full_content(content):
    """Print the full content for debugging"""
    print("\n==== FULL CONTENT ====")
    print(content)
    print("==== END OF CONTENT ====\n")

def test_parse():
    # Load the phase2_results.json file
    file_path = 'tests/phase_2_test/output/phase2_results.json'
    logger.info(f"Reading file: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        logger.info(f"JSON loaded successfully with keys: {list(data.keys())}")
        plan_content = data.get("plan", "")
        
        # Print the first 200 chars of the plan content
        logger.info(f"Plan content starts with: {plan_content[:200]}...")
        
        # Check if the plan contains agent definitions
        agent_count = len(re.findall(r'<agent_\d+', plan_content))
        logger.info(f"Found {agent_count} agent_X tags in the content")
        
        # Try direct regex extraction
        logger.info("Attempting direct regex extraction...")
        agent_blocks = re.findall(r'<agent_(\d+)[^>]*>.*?</agent_\d+>', plan_content, re.DOTALL)
        logger.info(f"Direct regex found {len(agent_blocks)} agent blocks")
        
        # Try fallback extraction
        logger.info("Attempting fallback extraction method...")
        agents_fallback = extract_agent_fallback(plan_content)
        logger.info(f"Fallback extraction found {len(agents_fallback)} agents")
        
        for i, agent in enumerate(agents_fallback):
            logger.info(f"  - Agent {i+1}: {agent.get('name')} with {len(agent.get('file_assignments', []))} files")
        
        # Try the full parse_agents_from_phase2 function
        logger.info("Attempting full parsing...")
        agents = parse_agents_from_phase2(plan_content)
        logger.info(f"Full parsing found {len(agents)} agents")
        
        for i, agent in enumerate(agents):
            logger.info(f"  - Agent {i+1}: {agent.get('name')} with {len(agent.get('file_assignments', []))} files")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parse() 