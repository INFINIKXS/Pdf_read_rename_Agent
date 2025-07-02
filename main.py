
from dotenv import load_dotenv
import click
from src.agent_core.rename_workflow import rename_mode
from src.agent_core.research_workflow import research_filter_mode


# Load environment variables from .env at the very start
load_dotenv()

@click.group()
def cli():
    pass


@cli.command()
def rename():
    """Run Rename Mode."""
    rename_mode()


@cli.command()
def research():
    """Run Research Filter Mode."""
    research_filter_mode()


if __name__ == "__main__":
    cli()
