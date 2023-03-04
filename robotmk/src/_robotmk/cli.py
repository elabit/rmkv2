import click

import robotmk.modes as modes
from robotmk.modes.agent import cli as agent_cli
from robotmk.modes.specialagent import cli as specialagent_cli
from robotmk.modes.robot import cli as robot_cli
from robotmk.modes.output import cli as output_cli


# TODO: options do not work here
# @click.option('--version', is_flag=True, help="Print version and exit")
# @click.option('--verbose', is_flag=True, help="Enable verbose mode")
@click.group(invoke_without_command=True)
@click.pass_context
def main(context):
    print(__name__ + ": " + "(cli main)")
    if context.invoked_subcommand is None:
        modes.run_output()
    else:
        # if context.opts["verbose"]:
        #     print(__name__ + ": " + f"robotmk_agent version: {__version__}")
        # print(__name__ + ": " + f"Invoked subcommand: {context.invoked_subcommand}")
        pass


# --------------------------------------------------
# AGENT


@main.group(
    name="agent",
    help="Execute Robotmk agent (Windows/Linux).",
    invoke_without_command=False,
)
# do not execute without subcommand
def cli_agent():
    print(__name__ + ": " + "(cli_agent)")
    pass


cli_agent.add_command(agent_cli.fg)
cli_agent.add_command(agent_cli.bg)
# cli_agent.add_command(agent_cli.stop)
# cli_agent.add_command(agent_cli.restart)

# --------------------------------------------------
# SPECIAL AGENT


@main.group(
    name="specialagent",
    help="Execute Robotmk as Special Agent (Checkmk).",
    invoke_without_command=True,
)
def cli_specialagent():
    modes.run_specialagent()


cli_specialagent.add_command(specialagent_cli.yyyy)


# --------------------------------------------------
# OUTPUT


@main.group(
    name="output",
    help="Produce Robotmk Agent output for Checkmk.",
    invoke_without_command=True,
)
def cli_output():
    modes.run_output()


cli_output.add_command(output_cli.yyyy)


# --------------------------------------------------
# ROBOT


@main.group(
    name="robot",
    help="Execute a single Robot (=Robot Framework suite).",
    invoke_without_command=True,
)
def cli_robot():
    modes.run_robot()


cli_specialagent.add_command(robot_cli.yyyy)

# --------------------------------------------------
if __name__ == "__main__":
    main()
