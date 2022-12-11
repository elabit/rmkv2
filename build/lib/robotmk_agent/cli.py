import click
from robotmk_agent import __version__, run_agent, run_specialagent, run_robot, env2conf
from .agent import cli as agent_cli
from .specialagent import cli as specialagent_cli

# TODO: options do not work here
# @click.option('--version', is_flag=True, help="Print version and exit")
# @click.option('--verbose', is_flag=True, help="Enable verbose mode")
@click.group(invoke_without_command=True)
@click.pass_context
def main(context):
    print("(cli main) Hello World!")
    if context.invoked_subcommand is None:
        run_agent()
    else:
        # if context.opts["verbose"]:
        #     print(f"robotmk_agent version: {__version__}")
        print(f"Invoked subcommand: {context.invoked_subcommand}")


@main.group(name="agent", invoke_without_command=False)
def cli_agent():
    run_agent()


cli_agent.add_command(agent_cli.start)
cli_agent.add_command(agent_cli.stop)
cli_agent.add_command(agent_cli.restart)


@main.group(name="specialagent", help="lala", invoke_without_command=True)
def cli_specialagent():
    run_specialagent()


cli_specialagent.add_command(specialagent_cli.yyyy)


@main.command(name="robot")
def cli_robot():
    run_robot()


if __name__ == "__main__":
    main()
