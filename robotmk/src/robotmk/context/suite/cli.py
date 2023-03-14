"""Robotmk suite CLI commands

Executes a single Robotmk suite."""
import click


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
@click.argument("suite", required=False)
def suite(ctx, vars, suite):
    click.echo("Executing suite %s" % suite)
    pass


@suite.command()
@click.pass_context
def vardump(ctx):
    click.echo("vardump")
    pass
