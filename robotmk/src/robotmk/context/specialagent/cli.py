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
def specialagent(ctx, vars):
    click.echo("Executing specialagent....")
    ctx.obj = Robotmk("specialagent", vars=vars)
    ctx.obj.config.set("common.context", "specialagent")

    pass


@specialagent.command()
@click.pass_context
def sequencer(ctx):
    click.secho("sequencer", fg="green")
    ctx.obj.execute()


@specialagent.command()
@click.pass_context
def output(ctx):
    click.secho("output", fg="green")
    ctx.obj.output()
    pass


@specialagent.command(help="Dump the config as YML to STDOUT or FILE")
# add file arg
@click.argument("file", required=False, type=click.Path(exists=False))
@click.pass_context
def ymldump(ctx, file):
    click.secho(ctx.obj.config.to_yml(file), fg="bright_white")
    sys.exit(0)
