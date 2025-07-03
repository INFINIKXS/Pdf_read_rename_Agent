
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
def rename():
    """
    Run Rename Mode.
    Scans for TXT, PDF, and DOCX files, extracts text, and uses the LLM to generate descriptive filenames.
    """
    rename_mode()



@cli.command()
def research():
    """
    Run Research Filter Mode.
    Scans a directory for PDFs, uses the LLM to score/filter them, and copies relevant files to a target directory.
    """
    research_filter_mode()


if __name__ == "__main__":
    cli()
