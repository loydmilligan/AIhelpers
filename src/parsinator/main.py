#!/usr/bin/env python3
"""
Parsinator CLI entry point with enhanced task generation
"""
import sys
import os
from pathlib import Path
import json

# Add the src directory to Python path so we can import parsinator modules
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

import click
from parsinator.utils import FileHandler, FileIOError
from parsinator.parser import BriefParser, ParsingError
from parsinator.templates import TemplateManager
from parsinator.id_manager import TaskIDManager
from parsinator.enhanced_generator import EnhancedTaskGenerator, TaskGenerationError

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
@click.option('--validate-only', is_flag=True, help='Only validate the brief without processing')
@click.option('--project-name', default='Generated Project', help='Name for the generated project')
def process_brief(brief_file, output_dir, existing_tasks, validate_only, project_name):
    """Process a single brief file and generate tasks"""
    try:
        if validate_only:
            # Just validate the brief format
            parser = BriefParser()
            try:
                brief_content = parser.parse_brief_file(brief_file)
                click.echo(f"✅ Brief validation successful!")
                click.echo(f"   Title: {brief_content.title}")
                click.echo(f"   Type: {brief_content.brief_type}")
                click.echo(f"   Tasks found: {len(brief_content.tasks)}")
                click.echo(f"   Description: {brief_content.description[:100]}...")
                return
            except ParsingError as e:
                click.echo(f"❌ Brief validation failed: {e}")
                sys.exit(1)
        
        click.echo(f"🚀 Processing brief file: {brief_file}")
        
        # Initialize enhanced task generator
        generator = EnhancedTaskGenerator(existing_tasks)
        
        # Process the brief file
        collection = generator.process_brief_files([brief_file])
        
        click.echo(f"✅ Successfully generated tasks!")
        
        # Show generation summary
        summary = generator.get_generation_summary()
        click.echo(f"\n📊 Generation Summary:")
        click.echo(f"   Tasks generated: {summary['id_management']['total_tasks']}")
        click.echo(f"   New tasks: {summary['id_management']['new_tasks']}")
        if summary['id_management']['existing_tasks'] > 0:
            click.echo(f"   Existing tasks: {summary['id_management']['existing_tasks']}")
        
        click.echo(f"   Priority distribution:")
        for priority, count in summary['id_management']['priority_distribution'].items():
            click.echo(f"      {priority}: {count}")
        
        # Show dependency analysis results
        if 'dependency_analysis' in summary and summary['dependency_analysis']:
            dep_summary = summary['dependency_analysis']
            click.echo(f"\n🔗 Dependency Analysis:")
            click.echo(f"   Dependencies suggested: {dep_summary.get('dependencies_suggested', 0)}")
            
            if 'confidence_distribution' in dep_summary:
                conf_dist = dep_summary['confidence_distribution']
                click.echo(f"   High confidence: {conf_dist.get('high_confidence', 0)}")
                click.echo(f"   Medium confidence: {conf_dist.get('medium_confidence', 0)}")
                click.echo(f"   Low confidence: {conf_dist.get('low_confidence', 0)}")
            
            if dep_summary.get('warnings'):
                click.echo(f"   ⚠️  Warnings: {len(dep_summary['warnings'])}")
                for warning in dep_summary['warnings'][:3]:  # Show first 3
                    click.echo(f"      • {warning}")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate tasks.json
        tasks_json_path = output_path / "tasks.json"
        generator.generate_tasks_json(str(tasks_json_path), project_name)
        
        click.echo(f"\n💾 Output generated:")
        click.echo(f"   tasks.json: {tasks_json_path}")
        
        # Show next steps
        click.echo(f"\n🎯 Next Steps:")
        click.echo(f"   1. Review generated tasks.json")
        click.echo(f"   2. Individual task files will be generated in Task 10")
        click.echo(f"   3. Run dependency mapping validation")
        
        unlocked_tasks = collection.get_unlocked_tasks()
        if unlocked_tasks:
            click.echo(f"\n🔓 Ready to start: {len(unlocked_tasks)} unlocked tasks")
            for task in unlocked_tasks[:3]:  # Show first 3
                click.echo(f"   • Task {task.id}: {task.title}")
            if len(unlocked_tasks) > 3:
                click.echo(f"   ... and {len(unlocked_tasks) - 3} more")
        
    except FileIOError as e:
        click.echo(f"❌ File error: {e}")
        sys.exit(1)
    except ParsingError as e:
        click.echo(f"❌ Parsing error: {e}")
        sys.exit(1)
    except TaskGenerationError as e:
        click.echo(f"❌ Task generation error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.argument('briefs_directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output-dir', default='./output', help='Directory for generated files')
@click.option('--existing-tasks', type=click.Path(), help='Path to existing tasks.json for additive sessions')
@click.option('--validate-only', is_flag=True, help='Only validate briefs without processing')
@click.option('--project-name', default='Generated Project', help='Name for the generated project')
def process_briefs(briefs_directory, output_dir, existing_tasks, validate_only, project_name):
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
        
        if validate_only:
            # Validate all briefs
            parser = BriefParser()
            total_tasks = 0
            
            for brief_file in brief_files:
                click.echo(f"\n📖 Validating: {brief_file.name}")
                try:
                    brief_content = parser.parse_brief_file(str(brief_file))
                    total_tasks += len(brief_content.tasks)
                    click.echo(f"   ✅ Type: {brief_content.brief_type}, Tasks: {len(brief_content.tasks)}")
                except ParsingError as e:
                    click.echo(f"   ❌ Validation failed: {e}")
                    sys.exit(1)
            
            click.echo(f"\n✅ All {len(brief_files)} briefs validated successfully!")
            click.echo(f"   Total tasks found: {total_tasks}")
            return
        
        click.echo(f"\n🚀 Processing {len(brief_files)} brief files...")
        
        # Initialize enhanced task generator
        generator = EnhancedTaskGenerator(existing_tasks)
        
        # Process all brief files
        brief_paths = [str(bf) for bf in brief_files]
        collection = generator.process_brief_files(brief_paths)
        
        click.echo(f"✅ Successfully processed all briefs!")
        
        # Show detailed generation summary
        summary = generator.get_generation_summary()
        click.echo(f"\n📊 Comprehensive Generation Summary:")
        click.echo(f"   Briefs processed: {summary['brief_processing']['briefs_processed']}")
        
        # Show brief breakdown
        click.echo(f"   Brief types:")
        for brief_type, count in summary['brief_processing']['brief_types'].items():
            if count > 0:
                click.echo(f"      {brief_type}: {count}")
        
        # Show task statistics
        click.echo(f"   Total tasks: {summary['id_management']['total_tasks']}")
        click.echo(f"   New tasks: {summary['id_management']['new_tasks']}")
        if summary['id_management']['existing_tasks'] > 0:
            click.echo(f"   Existing tasks: {summary['id_management']['existing_tasks']}")
        
        click.echo(f"   Priority distribution:")
        for priority, count in summary['id_management']['priority_distribution'].items():
            if count > 0:
                click.echo(f"      {priority}: {count}")
        
        # Show dependency analysis results
        if 'dependency_analysis' in summary and summary['dependency_analysis']:
            dep_summary = summary['dependency_analysis']
            click.echo(f"\n🔗 Advanced Dependency Analysis:")
            click.echo(f"   Dependencies suggested: {dep_summary.get('dependencies_suggested', 0)}")
            
            if 'dependency_statistics' in dep_summary:
                dep_stats = dep_summary['dependency_statistics']
                click.echo(f"   Dependency density: {dep_stats.get('dependency_density', 0):.2f}")
                click.echo(f"   Average confidence: {dep_stats.get('average_confidence', 0):.2f}")
            
            if 'confidence_distribution' in dep_summary:
                conf_dist = dep_summary['confidence_distribution']
                click.echo(f"   Confidence levels:")
                click.echo(f"      High (>= 0.8): {conf_dist.get('high_confidence', 0)}")
                click.echo(f"      Medium (0.5-0.8): {conf_dist.get('medium_confidence', 0)}")
                click.echo(f"      Low (< 0.5): {conf_dist.get('low_confidence', 0)}")
            
            if dep_summary.get('warnings'):
                click.echo(f"   ⚠️  Analysis Warnings: {len(dep_summary['warnings'])}")
                for warning in dep_summary['warnings'][:3]:  # Show first 3
                    click.echo(f"      • {warning}")
                if len(dep_summary['warnings']) > 3:
                    click.echo(f"      ... and {len(dep_summary['warnings']) - 3} more")
        
        # Show per-brief details
        click.echo(f"\n📋 Per-Brief Details:")
        for brief_info in summary['brief_processing']['briefs_by_file']:
            click.echo(f"   {brief_info['file']} ({brief_info['type']}):")
            click.echo(f"      Title: {brief_info['title']}")
            click.echo(f"      Tasks extracted: {brief_info['tasks_extracted']}")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate tasks.json
        tasks_json_path = output_path / "tasks.json"
        generator.generate_tasks_json(str(tasks_json_path), project_name)
        
        # Also save generation summary
        summary_path = output_path / "generation_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        click.echo(f"\n💾 Output generated:")
        click.echo(f"   tasks.json: {tasks_json_path}")
        click.echo(f"   generation_summary.json: {summary_path}")
        
        # Show dependency validation
        validation_errors = collection.validate_dependencies()
        if validation_errors:
            click.echo(f"\n⚠️  Dependency Validation Warnings:")
            for error in validation_errors:
                click.echo(f"   • {error}")
        else:
            click.echo(f"\n✅ All task dependencies validated successfully!")
        
        # Show ready tasks
        unlocked_tasks = collection.get_unlocked_tasks()
        click.echo(f"\n🔓 Ready to start: {len(unlocked_tasks)} unlocked tasks")
        for task in unlocked_tasks[:5]:  # Show first 5
            click.echo(f"   • Task {task.id}: {task.title}")
        if len(unlocked_tasks) > 5:
            click.echo(f"   ... and {len(unlocked_tasks) - 5} more")
        
        click.echo(f"\n🎯 Next Steps:")
        click.echo(f"   1. Review generated tasks.json")
        click.echo(f"   2. Individual task files will be generated in Task 10")
        click.echo(f"   3. Begin work on unlocked tasks")
        
    except FileIOError as e:
        click.echo(f"❌ File error: {e}")
        sys.exit(1)
    except TaskGenerationError as e:
        click.echo(f"❌ Task generation error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.argument('brief_file', type=click.Path(exists=True))
@click.option('--template-type', help='Template type to validate against (setup/feature/deployment)')
def validate_brief(brief_file, template_type):
    """Validate that a brief file follows the correct format"""
    try:
        parser = BriefParser()
        template_manager = TemplateManager()
        
        click.echo(f"🔍 Validating brief file: {brief_file}")
        
        # Parse the brief using our new parser
        brief_content = parser.parse_brief_file(brief_file)
        
        click.echo(f"✅ Brief parsing successful!")
        click.echo(f"   Title: {brief_content.title}")
        click.echo(f"   Detected type: {brief_content.brief_type}")
        click.echo(f"   Tasks found: {len(brief_content.tasks)}")
        
        # Also validate against templates
        handler = FileHandler()
        content = handler.read_brief_file(brief_file)
        report = template_manager.get_validation_report(content, template_type)
        click.echo(f"\n📋 Template Validation:")
        click.echo(report)
        
    except FileIOError as e:
        click.echo(f"❌ File error: {e}")
        sys.exit(1)
    except ParsingError as e:
        click.echo(f"❌ Parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        sys.exit(1)

@cli.command()
def list_templates():
    """List available brief templates"""
    try:
        template_manager = TemplateManager()
        report = template_manager.list_templates()
        click.echo(report)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

@cli.command()
@click.argument('brief_file', type=click.Path(exists=True))
def analyze_brief(brief_file):
    """Analyze a brief file and show detailed parsing results"""
    try:
        parser = BriefParser()
        
        click.echo(f"🔍 Analyzing brief file: {brief_file}")
        brief_content = parser.parse_brief_file(brief_file)
        
        click.echo(f"\n📄 Brief Analysis:")
        click.echo(f"   File: {brief_content.file_path.name}")
        click.echo(f"   Title: {brief_content.title}")
        click.echo(f"   Type: {brief_content.brief_type}")
        click.echo(f"   Description: {brief_content.description}")
        
        click.echo(f"\n📋 Tasks ({len(brief_content.tasks)}):")
        for i, task in enumerate(brief_content.tasks, 1):
            click.echo(f"   {i}. {task}")
        
        click.echo(f"\n📊 Metadata:")
        for key, value in brief_content.metadata.items():
            if isinstance(value, str) and len(value) > 80:
                value = value[:80] + "..."
            click.echo(f"   {key}: {value}")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing brief: {e}")
        sys.exit(1)

@cli.command()
@click.argument('tasks_json_file', type=click.Path(exists=True))
def analyze_tasks(tasks_json_file):
    """Analyze a generated tasks.json file"""
    try:
        handler = FileHandler()
        tasks_data = handler.read_tasks_json(tasks_json_file)
        
        click.echo(f"🔍 Analyzing tasks file: {tasks_json_file}")
        
        tasks = tasks_data.get('master', {}).get('tasks', [])
        metadata = tasks_data.get('master', {}).get('metadata', {})
        
        click.echo(f"\n📊 Task Analysis:")
        click.echo(f"   Total tasks: {len(tasks)}")
        
        # Analyze by status
        status_counts = {}
        for task in tasks:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        click.echo(f"   Status distribution:")
        for status, count in status_counts.items():
            click.echo(f"      {status}: {count}")
        
        # Analyze by priority
        priority_counts = {}
        for task in tasks:
            priority = task.get('priority', 'unknown')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        click.echo(f"   Priority distribution:")
        for priority, count in priority_counts.items():
            click.echo(f"      {priority}: {count}")
        
        # Analyze dependencies
        no_deps = len([t for t in tasks if not t.get('dependencies', [])])
        has_deps = len(tasks) - no_deps
        
        click.echo(f"   Dependencies:")
        click.echo(f"      No dependencies: {no_deps}")
        click.echo(f"      Has dependencies: {has_deps}")
        
        # Show metadata
        click.echo(f"\n📋 Metadata:")
        for key, value in metadata.items():
            click.echo(f"   {key}: {value}")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing tasks: {e}")
        sys.exit(1)

@cli.command()
@click.argument('briefs_directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--existing-tasks', type=click.Path(), help='Path to existing tasks.json for additive sessions')
@click.option('--confidence-threshold', default=0.5, help='Minimum confidence threshold for showing dependencies')
def analyze_dependencies(briefs_directory, existing_tasks, confidence_threshold):
    """Perform detailed dependency analysis on brief files"""
    try:
        click.echo(f"🔗 Analyzing dependencies in: {briefs_directory}")
        
        # Initialize enhanced task generator
        generator = EnhancedTaskGenerator(existing_tasks)
        
        # Process briefs to generate tasks and dependencies
        collection = generator.process_brief_files([])  # We'll process directory
        handler = FileHandler()
        brief_files = handler.find_brief_files(briefs_directory)
        brief_paths = [str(bf) for bf in brief_files]
        collection = generator.process_brief_files(brief_paths)
        
        # Get detailed dependency analysis
        dep_analysis = generator.get_dependency_analysis()
        
        if not dep_analysis:
            click.echo("❌ No dependency analysis available")
            return
        
        click.echo(f"\n📊 Detailed Dependency Analysis:")
        click.echo(f"   Total dependencies suggested: {len(dep_analysis.suggested_dependencies)}")
        
        # Show dependencies by confidence level
        high_conf = [d for d in dep_analysis.suggested_dependencies if d.confidence >= 0.8]
        medium_conf = [d for d in dep_analysis.suggested_dependencies if 0.5 <= d.confidence < 0.8]
        low_conf = [d for d in dep_analysis.suggested_dependencies if d.confidence < 0.5]
        
        click.echo(f"   High confidence (>= 0.8): {len(high_conf)}")
        click.echo(f"   Medium confidence (0.5-0.8): {len(medium_conf)}")
        click.echo(f"   Low confidence (< 0.5): {len(low_conf)}")
        
        # Show dependencies by type
        type_counts = {}
        for dep in dep_analysis.suggested_dependencies:
            type_counts[dep.relationship_type] = type_counts.get(dep.relationship_type, 0) + 1
        
        click.echo(f"\n📋 Dependencies by Type:")
        for dep_type, count in type_counts.items():
            click.echo(f"   {dep_type}: {count}")
        
        # Show detailed dependencies above threshold
        filtered_deps = [d for d in dep_analysis.suggested_dependencies if d.confidence >= confidence_threshold]
        
        if filtered_deps:
            click.echo(f"\n🔍 Dependencies (confidence >= {confidence_threshold}):")
            for dep in filtered_deps[:10]:  # Show first 10
                click.echo(f"   Task {dep.from_task_id} → Task {dep.to_task_id}")
                click.echo(f"      Type: {dep.relationship_type}")
                click.echo(f"      Confidence: {dep.confidence:.2f}")
                click.echo(f"      Reason: {dep.reason}")
                click.echo()
            
            if len(filtered_deps) > 10:
                click.echo(f"   ... and {len(filtered_deps) - 10} more dependencies")
        
        # Show warnings
        if dep_analysis.warnings:
            click.echo(f"\n⚠️  Analysis Warnings:")
            for warning in dep_analysis.warnings:
                click.echo(f"   • {warning}")
        
        # Show statistics
        if dep_analysis.statistics:
            stats = dep_analysis.statistics
            click.echo(f"\n📈 Statistics:")
            click.echo(f"   Dependency density: {stats.get('dependency_density', 0):.3f}")
            click.echo(f"   Average confidence: {stats.get('average_confidence', 0):.3f}")
            click.echo(f"   Tasks with dependencies: {stats.get('tasks_with_dependencies', 0)}")
        
    except Exception as e:
        click.echo(f"❌ Error analyzing dependencies: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    cli()