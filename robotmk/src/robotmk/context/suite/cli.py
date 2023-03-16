"""Robotmk suite CLI commands

Executes a single Robotmk suite."""
import sys
import click
from robotmk.main import Robotmk, DEFAULTS


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--yml", "-y", help="Read config from custom YML file")
@click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
@click.option(
    "--ymldump", "-Y", is_flag=True, help="Prints the config as YML and exits"
)
@click.argument("suite", required=False)
def suite(ctx, yml, vars, suite, ymldump):
    if vars and yml:
        raise click.BadParameter("Cannot use --yml and --vars at the same time")
    click.echo("suite")
    ctx.robotmk = Robotmk("suite", yml=yml, vars=vars)
    if ymldump:
        click.secho(ctx.robotmk.config.to_yml(), fg="bright_white")
        sys.exit(0)


@suite.command()
@click.pass_context
def vardump(ctx):
    click.echo("vardump")
    pass
