"""Robotmk CLI Interface. 

Start Robotmk in different contexts.
Context command can also be set via environment variable ROBOTMK_common_context."""
import click
from robotmk.main import Robotmk, DEFAULTS, LOG_LEVELS
import importlib
import pkgutil
import os.path
import warnings


# CMD1        CMD2     OPTION                                    CMD3            # Description
# ---------------------------------------------------------------------------------------------
# # LOCAL CONTEXT
# robotmk                                                                        # no arg = print output

# robotmk     local                                              output          # print output
# robotmk     local    --yml /etc/checkmk/another_robotmk.yml    output          # print output with yml
# robotmk     local    --vars /var/robotmk_local.env             output          # print output, load env from file (instead of env)

# robotmk     local                                              scheduler       # start scheduler
# robotmk     local    --yml /etc/checkmk/another_robotmk.yml    scheduler       # start scheduler with yml
# robotmk     local    --vars /var/robotmk_local.env             scheduler       # start scheduler, load env from file  (instead of env)
# ---------------------------------------------------------------------------------------------
# # SUITE CONTEXT
# robotmk                                                                        # no arg = exec suite as configured in env
# robotmk     suite    --vars /var/rmk/foosuiteA_8bb36c3.env                     # exec suite with env from file and suite = yml -> common: suite)
# robotmk     suite    --vars /var/rmk/foosuiteA_8bb36c3.env     bazsuite        # exec suite with env from file and suite = bazsuite
# robotmk     suite                                              vardump  foobarsuiteA   # just dump the vars for foobarsuiteA
# ---------------------------------------------------------------------------------------------
# # SPECIALAGENT (="s.a."") CONTEXT
# robotmk                                                                        # no arg = seq & output
# (robotmk    s.a.     output)                                                   # NOT POSSIBLE - no config file
# robotmk     s.a.     --vars ~/var/robotmk/s.a.-hostfoo.env     output          # run output with env from file

# (robotmk    s.a.     sequencer)                                                # NOT POSSIBLE - no config file
# robotmk     s.a.     --vars ~/var/robotmk/s.a.-hostfoo.env     sequencer       # run requencer with env from file


def get_commands_from_pkg(pkg) -> dict:
    """CLI options for the contexts are defined within the context packages within cli.py module.

    Each sub-PACKAGE of pkg is considered a sub-COMMAND. This function recursively traverses the
    package tree and returns all function objects which have the same name as the package.

    This allows to maintain the CLI logic within the context packages, while still having a single
    entry point for the CLI.

    Example:
    robotmk.context.local.cli.py contains a function called local(), decorated with @click.group()
    and connected with subcomands "output()" and "scheduler()". The discovered subcommand is "local()".
    """
    pkg_obj = importlib.import_module(pkg)
    pkg_path = os.path.dirname(pkg_obj.__file__)
    commands = {}
    for module in pkgutil.iter_modules([pkg_path]):
        module_obj = importlib.import_module(f"{pkg}.{module.name}")
        if module.ispkg:
            cmd_from_pkg = get_commands_from_pkg(f"{pkg}.{module.name}")
            commands.update(cmd_from_pkg)
        else:
            if module.name == "cli":
                cli_functions = [f for f in dir(module_obj) if f == pkg.split(".")[-1]]

                for cli_function in cli_functions:
                    commands[cli_function] = getattr(module_obj, cli_function)

    return commands


# Create the main group and assign the subcommands gathered from the context packages
@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=__doc__,
    invoke_without_command=True,
    commands=get_commands_from_pkg("robotmk.context"),
)
@click.option(
    "--loglevel",
    "-l",
    default=DEFAULTS["common"]["log_level"],
    type=click.Choice(LOG_LEVELS),
)
@click.pass_context
def main(ctx, loglevel):
    if ctx.invoked_subcommand is None:
        # robotmk was called without argument. Try to detect the context from the default
        # config and/or environment variables.
        # After that run the default subcommand of the context:
        # - local: produce output
        # - specialagent: produce output + call sequencer
        # - suite: run a single suite
        ctx.robotmk = Robotmk(
            contextname=None, log_level=loglevel, ymlfile=None, varfile=None
        )
        ctx.robotmk.run_default()
    else:
        # Robotmk was executed with a context subcommand, whose logic is defined within the context.
        pass


@main.command()
def diagnose():
    """Print diagnostic information."""
    click.secho("diagnose", fg="yellow")
    # TODO implement diagnose()
    # - environment with ROBOTOMK vars
    # YML present?
    # RCC present
    # OS
    # Python version
    # Robotmk version
    # Robot version
    # configdump
    # create a dummy suite with api and run it in suite mode
    # CPU cores
    # RAM
    # disk space
    # network

    pass


if __name__ == "__main__":
    main()
