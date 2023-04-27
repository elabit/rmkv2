"""CLI commands for the agent context. 

Executes the Robotmk scheduler on Windows & Linux, produces Checkmk Agent output"""
import sys
import click
from robotmk.main import Robotmk, DEFAULTS


#                         | |
#    __ _  __ _  ___ _ __ | |_
#   / _` |/ _` |/ _ \ '_ \| __|
#  | (_| | (_| |  __/ | | | |_
#   \__,_|\__, |\___|_| |_|\__|
#          __/ |
#         |___/


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--yml", "-y", help="Read config from custom YML file")

# @click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
def agent(ctx, yml):
    ctx_loglevel = ctx.parent.params.get("loglevel", DEFAULTS["common"]["log_level"])
    ctx.obj = Robotmk(contextname="agent", log_level=ctx_loglevel, ymlfile=yml)
    if ctx.invoked_subcommand is None:
        click.secho("No subcommand given. Use --help for help.", fg="red")
        sys.exit(1)


@agent.command()
@click.pass_context
def scheduler(ctx):
    """Starts the scheduler to execute tests repeatedly."""
    ctx.obj.execute()


@agent.command()
@click.pass_context
def output(ctx):
    """Emits Checkmk Agent output for all suite results."""
    data = ctx.obj.output()
    click.secho(data, fg="bright_white")


@agent.command(help="Dumps the config as YML to STDOUT or FILE")
# add file arg
@click.argument("file", required=False, type=click.Path(exists=False))
@click.pass_context
def ymldump(ctx, file):
    click.secho(ctx.obj.config.to_yml(file), fg="bright_white")
    sys.exit(0)
