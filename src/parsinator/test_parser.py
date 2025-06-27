#!/usr/bin/env python3
"""
Test the Brief Parser Engine with actual brief files
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from parsinator.parser import BriefParser
from parsinator.models import BriefContent

def test_parser_with_brief_files():
    """Test parser with the actual brief files"""
    print("🧪 Testing Brief Parser Engine")
    print("=" * 50)
    
    parser = BriefParser()
    
    # Test with the parsinator brief files
    brief_files = [
        "docs/parsinator/briefs/parsinator_setup_brief.md",
        "docs/parsinator/briefs/parsinator_feature_brief.md", 
        "docs/parsinator/briefs/parsinator_deployment_brief.md"
    ]
    
    for brief_file in brief_files:
        print(f"\n📄 Testing: {brief_file}")
        
        try:
            # Check if file exists
            if not Path(brief_file).exists():
                print(f"⚠️  File not found: {brief_file}")
                continue
            
            # Parse the brief
            brief_content = parser.parse_brief_file(brief_file)
            
            print(f"✅ Successfully parsed!")
            print(f"   Title: {brief_content.title}")
            print(f"   Type: {brief_content.brief_type}")
            print(f"   Description: {brief_content.description[:100]}...")
            print(f"   Tasks found: {len(brief_content.tasks)}")
            
            # Show first few tasks
            for i, task in enumerate(brief_content.tasks[:3]):
                print(f"   Task {i+1}: {task[:80]}...")
            
            if len(brief_content.tasks) > 3:
                print(f"   ... and {len(brief_content.tasks) - 3} more tasks")
            
            print(f"   Metadata: {brief_content.metadata}")
            
        except Exception as e:
            print(f"❌ Failed to parse {brief_file}: {e}")
            import traceback
            traceback.print_exc()

def test_parser_with_sample_content():
    """Test parser with sample brief content"""
    print("\n🧪 Testing with Sample Content")
    print("=" * 50)
    
    sample_setup_brief = """
# Project Setup Brief: Sample Project

## Problem Statement
We need to set up a basic project structure for development.

## Setup Scope
Create foundational infrastructure for the project.

## Core Setup Tasks
### Must-Have Infrastructure
1. **Initialize Git Repository**: Set up version control with proper branching strategy
2. **Create Directory Structure**: Establish standard project folders and organization
3. **Setup Dependencies**: Install and configure required libraries and tools
4. **Configure Environment**: Set up development environment variables and settings

### Optional Setup Tasks
1. **Add Docker Support**: Create Dockerfile for containerized development
2. **Setup CI/CD**: Configure automated testing and deployment pipelines

## Technical Requirements
- Python 3.8+
- Git version control
- Virtual environment support

## Success Criteria
- Developer can clone and run project within 5 minutes
- All dependencies install without errors
"""
    
    parser = BriefParser()
    
    try:
        # Write sample content to temporary file
        temp_file = Path("temp_setup_brief.md")
        temp_file.write_text(sample_setup_brief)
        
        # Parse the sample brief
        brief_content = parser.parse_brief_file(str(temp_file))
        
        print(f"✅ Sample parsing successful!")
        print(f"   Title: {brief_content.title}")
        print(f"   Type: {brief_content.brief_type}")
        print(f"   Tasks found: {len(brief_content.tasks)}")
        
        for i, task in enumerate(brief_content.tasks):
            print(f"   Task {i+1}: {task}")
        
        # Clean up
        temp_file.unlink()
        
    except Exception as e:
        print(f"❌ Sample parsing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser_with_brief_files()
    test_parser_with_sample_content()
    print("\n🎉 Parser testing complete!")
