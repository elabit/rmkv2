"""Robotmk specialagent CLI commands

Executes Robotmk in specialagent context. This CLI is rather used to debug the 
specialagent than to run it in production."""
import click


# use module docstring as help text
@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
@click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
def specialagent(ctx, vars):
    click.echo("Executing specialagent....")
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
