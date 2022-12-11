import click
from robotmk_agent import (
    run_agent,
    run_specialagent,
    run_robot,
    run_output,
    __version__,
)
from robotmk_agent.robotmk.agent_host import cli as agent_cli
from robotmk_agent.robotmk.agent_special import cli as specialagent_cli
from robotmk_agent.robotmk.robot import cli as robot_cli
from robotmk_agent.robotmk.output import cli as output_cli

# TODO: options do not work here
# @click.option('--version', is_flag=True, help="Print version and exit")
# @click.option('--verbose', is_flag=True, help="Enable verbose mode")
@click.group(invoke_without_command=True)
@click.pass_context
def main(context):
    print("(cli main) Hello World!")
    if context.invoked_subcommand is None:
        run_output()
    else:
        # if context.opts["verbose"]:
        #     print(f"robotmk_agent version: {__version__}")
        print(f"Invoked subcommand: {context.invoked_subcommand}")


# --------------------------------------------------


@main.group(
    name="agent",
    help="Execute Robotmk as daemonized agent (Windows/Linux).",
    invoke_without_command=False,
)
def cli_agent():
    run_agent()


cli_agent.add_command(agent_cli.start)
cli_agent.add_command(agent_cli.stop)
cli_agent.add_command(agent_cli.restart)

# --------------------------------------------------


@main.group(
    name="specialagent",
    help="Execute Robotmk as Special Agent (Checkmk).",
    invoke_without_command=True,
)
def cli_specialagent():
    run_specialagent()


cli_specialagent.add_command(specialagent_cli.yyyy)


# --------------------------------------------------


@main.group(
    name="output",
    help="Produce Robotmk Agent output for Checkmk.",
    invoke_without_command=True,
)
def cli_output():
    run_output()


cli_output.add_command(output_cli.yyyy)


# --------------------------------------------------


@main.group(
    name="robot",
    help="Execute a single Robot (=Robot Framework suite).",
    invoke_without_command=True,
)
def cli_robot():
    run_robot()


cli_specialagent.add_command(robot_cli.yyyy)

# --------------------------------------------------

if __name__ == "__main__":
    main()
