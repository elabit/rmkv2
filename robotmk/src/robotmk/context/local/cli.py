"""Robotmk local CLI commands

Executes Robotmk in local context (Windows & Linux)"""
import sys
import click
from robotmk.main import Robotmk, DEFAULTS


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--yml", "-y", help="Read config from custom YML file")
@click.option(
    "--ymldump", "-Y", is_flag=True, help="Prints the config as YML and exits"
)
# @click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
def local(ctx, yml, ymldump):
    ctx.robotmk = Robotmk("local", yml=yml)
    if ymldump:
        click.secho(ctx.robotmk.config.to_yml(), fg="bright_white")
        sys.exit(0)
    if ctx.invoked_subcommand is None:
        click.secho("No subcommand given. Use --help for help.", fg="red")
        sys.exit(1)
    else:
        pass


@local.command()
@click.pass_context
def output(ctx):
    click.secho("output", fg="green")
    pass


@local.command()
@click.pass_context
def scheduler(ctx):
    click.secho("scheduler", fg="green")
    pass
