"""Robotmk local CLI commands

Executes Robotmk in local context (Windows & Linux)"""
import click


# use module docstring as help text
@click.group(help=__doc__)
@click.pass_context
@click.option("--yml", "-y", help="Read config from custom YML file")
@click.option("--vars", "-v", help="Read vars from .env file (ignores environment)")
def local(ctx, yml, vars):
    click.echo("local")
    pass


@local.command()
@click.pass_context
def output(ctx):
    click.echo("output")
    pass


@local.command()
@click.pass_context
def scheduler(ctx):
    click.echo("scheduler")
    pass
