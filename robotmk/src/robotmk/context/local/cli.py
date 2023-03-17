"""CLI commands for the local context. 

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
    ctx.obj = Robotmk("local", yml=yml)
    if ymldump:
        click.secho(ctx.obj.config.to_yml(), fg="bright_white")
        sys.exit(0)
    if ctx.invoked_subcommand is None:
        click.secho("No subcommand given. Use --help for help.", fg="red")
        sys.exit(1)


@local.command()
@click.pass_context
def output(ctx):
    click.secho("output", fg="green")
    ctx.obj.produce_agent_output()
    pass


@local.command()
@click.pass_context
def scheduler(ctx):
    click.secho("scheduler", fg="green")
    ctx.obj.run()
    pass
