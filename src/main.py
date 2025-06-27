# Main entry point for the CLI
import click
from pathlib import Path
from prompt_generator import parse_template, assemble_prompt
from utils import save_as_json

@click.group()
def cli():
    """A CLI tool to help generate prompts for AI models."""
    pass

@cli.command()
@click.argument('template_path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def generate(template_path):
    """
    Generates a prompt from a template by asking the user for input.
    """
    template_file = Path(template_path)
    placeholders = parse_template(template_file)

    if not placeholders:
        click.echo(f"Error: No placeholders found in {template_file.name} or file is empty.")
        return

    click.echo(f"Please provide values for the following placeholders in {template_file.name}:")
    
    answers = {}
    for placeholder in placeholders:
        prompt_text = placeholder.replace('_', ' ').capitalize()
        answers[placeholder] = click.prompt(prompt_text)

    # Save the user's answers to a JSON file
    json_output_file = Path('prompt_data.json')
    save_as_json(answers, json_output_file)
    click.echo(f"\nSuccessfully saved prompt data to {json_output_file}")

    # Assemble the final prompt
    template_content = template_file.read_text()
    meta_prompt_path = Path('prompts/meta_prompt.md')
    final_prompt = assemble_prompt(template_content, answers, meta_prompt_path)

    # Get output file path from user
    output_path_str = click.prompt("Enter the path to save the generated prompt (e.g., path/to/file.md)", default="generated_prompt.md")
    output_file = Path(output_path_str)

    # Ensure the file has a .md extension
    if output_file.suffix != '.md':
        output_file = output_file.with_suffix('.md')

    # Save the final prompt to a file
    output_file.write_text(final_prompt)
    click.echo(f"Successfully generated prompt and saved to {output_file}")

if __name__ == '__main__':
    cli()