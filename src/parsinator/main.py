#!/usr/bin/env python3
"""
Parsinator CLI entry point
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path so we can import parsinator modules
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

import click
from parsinator.utils import FileHandler, FileIOError

@click.group()
@click.version_option()
def cli():
    """Parsinator - Convert project briefs to detailed task lists"""
    pass

@cli.command()
def hello():
    """Test command to verify CLI works"""
    click.echo("Parsinator is ready!")

@cli.command()
@click.option('--test-file', help='Test file to read')
def test_io(test_file):
    """Test file I/O functionality"""
    handler = FileHandler()
    
    if test_file:
        try:
            content = handler.read_brief_file(test_file)
            click.echo(f"✅ Successfully read {len(content)} characters from {test_file}")
        except Exception as e:
            click.echo(f"❌ Error reading file: {e}")
    else:
        click.echo("File I/O system ready!")

@cli.command()
@click.argument('brief_file', type=click.Path(exists=True))
@click.option('--output-dir', default='./output', help='Directory for generated files')
@click.option('--existing-tasks', type=click.Path(), help='Path to existing tasks.json for additive sessions')
def process_brief(brief_file, output_dir, existing_tasks):
    """Process a single brief file and generate tasks"""
    try:
        handler = FileHandler()
        
        # Read the brief file
        click.echo(f"📖 Reading brief file: {brief_file}")
        brief_content = handler.read_brief_file(brief_file)
        
        # Read existing tasks if provided
        existing_data = {}
        if existing_tasks:
            click.echo(f"📖 Reading existing tasks: {existing_tasks}")
            existing_data = handler.read_tasks_json(existing_tasks)
        
        # TODO: This will be implemented in later tasks
        click.echo(f"✅ Brief processing ready!")
        click.echo(f"   Brief file: {brief_file}")
        click.echo(f"   Output directory: {output_dir}")
        click.echo(f"   Existing tasks: {existing_tasks if existing_tasks else 'None'}")
        click.echo(f"   Brief content: {len(brief_content)} characters")
        
    except FileIOError as e:
        click.echo(f"❌ File error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
@click.argument('briefs_directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output-dir', default='./output', help='Directory for generated files')
@click.option('--existing-tasks', type=click.Path(), help='Path to existing tasks.json for additive sessions')
def process_briefs(briefs_directory, output_dir, existing_tasks):
    """Process multiple brief files in a directory"""
    try:
        handler = FileHandler()
        
        # Find all brief files
        click.echo(f"🔍 Finding brief files in: {briefs_directory}")
        brief_files = handler.find_brief_files(briefs_directory)
        
        if not brief_files:
            click.echo(f"❌ No .md brief files found in {briefs_directory}")
            sys.exit(1)
        
        click.echo(f"📁 Found {len(brief_files)} brief files:")
        for brief_file in brief_files:
            click.echo(f"   - {brief_file.name}")
        
        # Read existing tasks if provided
        existing_data = {}
        if existing_tasks:
            click.echo(f"📖 Reading existing tasks: {existing_tasks}")
            existing_data = handler.read_tasks_json(existing_tasks)
        
        # TODO: This will be implemented in later tasks
        click.echo(f"✅ Batch processing ready!")
        click.echo(f"   Briefs directory: {briefs_directory}")
        click.echo(f"   Output directory: {output_dir}")
        click.echo(f"   Existing tasks: {existing_tasks if existing_tasks else 'None'}")
        
    except FileIOError as e:
        click.echo(f"❌ File error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
@click.argument('brief_file', type=click.Path(exists=True))
@click.option('--template-type', help='Template type to validate against (setup/feature/deployment)')
def validate_brief(brief_file, template_type):
    """Validate that a brief file follows the correct format"""
    try:
        from parsinator.templates import TemplateManager
        
        handler = FileHandler()
        template_manager = TemplateManager()
        
        click.echo(f"🔍 Validating brief file: {brief_file}")
        brief_content = handler.read_brief_file(brief_file)
        
        # Get detailed validation report
        report = template_manager.get_validation_report(brief_content, template_type)
        click.echo(report)
        
    except FileIOError as e:
        click.echo(f"❌ File error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
def list_templates():
    """List available brief templates"""
    try:
        from parsinator.templates import TemplateManager
        
        template_manager = TemplateManager()
        report = template_manager.list_templates()
        click.echo(report)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli()