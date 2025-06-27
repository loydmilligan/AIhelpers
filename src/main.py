# Main entry point for the CLI
import click
from pathlib import Path
from prompt_generator import parse_template

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

    output_file = Path('prompt_data.json')
    save_as_json(answers, output_file)
    click.echo(f"\nSuccessfully saved prompt data to {output_file}")


if __name__ == '__main__':
    cli()