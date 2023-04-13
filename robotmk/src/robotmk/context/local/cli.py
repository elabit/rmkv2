"""CLI commands for the local context. 

Executes the Robotmk scheduler on Windows & Linux"""
import sys
import click
from robotmk.main import Robotmk, DEFAULTS


#   _                 _
#  | |               | |
#  | | ___   ___ __ _| |
#  | |/ _ \ / __/ _` | |
#  | | (_) | (_| (_| | |
#  |_|\___/ \___\__,_|_|


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--yml", "-y", help="Read config from custom YML file")

# @click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
def local(ctx, yml):
    ctx_loglevel = ctx.parent.params.get("loglevel", DEFAULTS["common"]["log_level"])
    ctx.obj = Robotmk(contextname="local", log_level=ctx_loglevel, ymlfile=yml)
    if ctx.invoked_subcommand is None:
        click.secho("No subcommand given. Use --help for help.", fg="red")
        sys.exit(1)


@local.command()
@click.pass_context
def scheduler(ctx):
    """Start the local scheduler to run RF suites."""

    click.secho("scheduler", fg="green")
    ctx.obj.execute()
    pass


@local.command()
@click.pass_context
def output(ctx):
    click.secho("output", fg="green")
    ctx.obj.output()
    pass


@local.command(help="Dump the config as YML to STDOUT or FILE")
# add file arg
@click.argument("file", required=False, type=click.Path(exists=False))
@click.pass_context
def ymldump(ctx, file):
    click.secho(ctx.obj.config.to_yml(file), fg="bright_white")
    sys.exit(0)
