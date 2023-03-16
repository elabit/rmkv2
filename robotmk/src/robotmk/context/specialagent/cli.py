"""CLI commands for the specialagent context.

Executes Robotmk in specialagent context. This CLI is rather used to debug the 
specialagent than to run it in production."""
import sys
import click
from robotmk.main import Robotmk, DEFAULTS


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
@click.option(
    "--ymldump", "-Y", is_flag=True, help="Prints the config as YML and exits"
)
def specialagent(ctx, vars, ymldump):
    click.echo("Executing specialagent....")
    ctx.robotmk = Robotmk("specialagent", vars=vars)
    if ymldump:
        click.secho(ctx.robotmk.config.to_yml(), fg="bright_white")
        sys.exit(0)

    pass


@specialagent.command()
@click.pass_context
def sequencer(ctx):
    click.echo("sequencer")
    pass


@specialagent.command()
@click.pass_context
def output(ctx):
    click.echo("output")
    pass
