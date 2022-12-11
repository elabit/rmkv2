import click

from robotmk.rmk.agent import cli as agent_cli
from robotmk.rmk.specialagent import cli as specialagent_cli
from robotmk.rmk.robot import cli as robot_cli
from robotmk.rmk.output import cli as output_cli

import robotmk.rmk as rmk

# TODO: options do not work here
# @click.option('--version', is_flag=True, help="Print version and exit")
# @click.option('--verbose', is_flag=True, help="Enable verbose mode")
@click.group(invoke_without_command=True)
@click.pass_context
def main(context):
    # print("(cli main) Hello World!")
    if context.invoked_subcommand is None:
        rmk.run_output()
    else:
        # if context.opts["verbose"]:
        #     print(f"robotmk_agent version: {__version__}")
        print(f"Invoked subcommand: {context.invoked_subcommand}")


# --------------------------------------------------
# AGENT


@main.group(
    name="agent",
    help="Execute Robotmk as daemonized agent (Windows/Linux).",
    invoke_without_command=False,
)
# do not execute without subcommand
def cli_agent():
    pass


cli_agent.add_command(agent_cli.start)
cli_agent.add_command(agent_cli.stop)
cli_agent.add_command(agent_cli.restart)

# --------------------------------------------------
# SPECIAL AGENT


@main.group(
    name="specialagent",
    help="Execute Robotmk as Special Agent (Checkmk).",
    invoke_without_command=True,
)
def cli_specialagent():
    rmk.run_specialagent()


cli_specialagent.add_command(specialagent_cli.yyyy)


# --------------------------------------------------
# OUTPUT


@main.group(
    name="output",
    help="Produce Robotmk Agent output for Checkmk.",
    invoke_without_command=True,
)
def cli_output():
    rmk.run_output()


cli_output.add_command(output_cli.yyyy)


# --------------------------------------------------
# ROBOT


@main.group(
    name="robot",
    help="Execute a single Robot (=Robot Framework suite).",
    invoke_without_command=True,
)
def cli_robot():
    rmk.run_robot()


cli_specialagent.add_command(robot_cli.yyyy)

# --------------------------------------------------

if __name__ == "__main__":
    main()
