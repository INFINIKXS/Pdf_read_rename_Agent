
from dotenv import load_dotenv
import click
from src.agent_core.rename_workflow import rename_mode
from src.agent_core.research_workflow import research_filter_mode


# Load environment variables from .env at the very start
load_dotenv()


@click.group()
def cli():
    """
    Main CLI group for the Document Intelligence Agent.
    Provides 'rename' and 'research' subcommands for document processing workflows.
    """
    pass





@cli.command()
@click.option('--target-dir', default=None, help='Source folder to scan for files to rename.')
@click.option('--dest-dir', default=None, help='Destination folder to copy and rename files.')
def rename(target_dir, dest_dir):
    """
    Run Rename Mode.
    Scans for TXT, PDF, and DOCX files, extracts text, and uses the LLM to generate descriptive filenames. Copies and renames files to the destination folder.
    """
    rename_mode(target_dir=target_dir, dest_dir=dest_dir)




@cli.command()
@click.option('--source-dir', default=None, help='Source folder to scan for PDFs.')
@click.option('--dest-dir', default=None, help='Destination folder to copy relevant PDFs.')
@click.option('--details-file', default='Research_details.md', help='Path to a .md file containing research topic, aim, questions, objectives, and rationale.')
def research(source_dir, dest_dir, details_file):
    """
    Run Research Filter Mode.
    Scans a directory for PDFs, uses the LLM to score/filter them, and copies relevant files to a target directory.
    """
    try:
        with open(details_file, 'r', encoding='utf-8') as f:
            research_details = f.read()
    except Exception as e:
        print(f"Failed to read research details file: {e}")
        return
    # Compose a prompt for the LLM using the research details
    query = (
        "Given the following research topic, aim, questions, objectives, and rationale, "
        "is this document relevant to the research? Reply with a score from 0 to 1.\n\n"
        f"{research_details}"
    )
    research_filter_mode(source_dir=source_dir, dest_dir=dest_dir, query=query)


if __name__ == "__main__":
    cli()
