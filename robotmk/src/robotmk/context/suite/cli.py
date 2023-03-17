"""CLI commands for execution of a single suite."""

import sys
import click
from robotmk.cli.defaultgroup import DefaultGroup
from robotmk.main import Robotmk, DEFAULTS


# use module docstring as help text
@click.group(
    cls=DefaultGroup, default_if_no_args=True, help=__doc__, invoke_without_command=True
)
@click.pass_context
@click.option("--yml", "-y", help="Read config from custom YML file")
@click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
def suite(ctx, yml, vars):
    if vars and yml:
        raise click.BadParameter("Cannot use --yml and --vars at the same time")
    click.echo("suite")
    ctx.robotmk = Robotmk("suite", yml=yml, vars=vars)


@suite.command(default=True)
@click.argument("suite", required=False)
@click.pass_context
def run(ctx, suite):
    """Run a single SUITE.

    SUITE is a directory or .robot file under $ROBOTDIR (can also be set by env:ROBOTMK_common_suite)
    """
    click.secho("run", fg="green")
    pass


@suite.command()
@click.argument("suite", required=True)
@click.option(
    "--number",
    "-n",
    help="Number of last execution logs of SUITE to show",
    default=1,
    show_default=True,
)
@click.option(
    "--pid", "-p", help="Shows the execution log of SUITE with a specific PID"
)
@click.pass_context
def logs(ctx, suite, number, pid):
    """Display the log files of a single SUITE.

    SUITE is a directory or .robot file under $ROBOTDIR (can also be set by env:ROBOTMK_common_suite)
    """
    click.secho("logs", fg="green")
    if int(number) != 1 and pid != None:
        raise click.BadParameter("Cannot use --number and --pid at the same time %d")
    click.echo("These are the logs of suite %s %d:" % (suite, number))
    pass


@suite.command(help="Dump the YML config to file or STDOUT")
# add file arg
@click.argument("file", required=False, type=click.Path(exists=False))
@click.pass_context
def ymldump(ctx, file):
    click.secho(ctx.robotmk.config.to_yml(file), fg="bright_white")
    sys.exit(0)


@suite.command()
@click.pass_context
def vardump(ctx):
    click.secho("vardump", fg="green")
    pass
