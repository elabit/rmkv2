"""Robotmk CLI Interface. 

Start Robotmk in different contexts"""
import click
from robotmk.main import Robotmk, DEFAULTS
import importlib
import pkgutil
import os.path
from functools import wraps


# def add_parent(parent):
#     def decorator(func):
#         func.parent = parent
#         return func

#     return decorator


# @add_parent("my_parent")
# def my_function():
#     pass


# print(my_function.parent)  # prints "my_parent"


# CMD1        CMD2     CMD3         OPT1 OPT2 OPT3
# ---------------------------------------------------------------------------------------------
# # LOCAL CONTEXT
# robotmk                                                                        # no arg = print output

# robotmk     local    output                                                    # print output
# robotmk     local    output       --yml /etc/checkmk/another_robotmk.yml       # print output with yml
# robotmk     local    output       --vars /var/robotmk_local.env                # print output, load env from file (instead of env)

# robotmk     local    scheduler                                                 # start scheduler
# robotmk     local    scheduler    --yml /etc/checkmk/another_robotmk.yml       # start scheduler with yml
# robotmk     local    scheduler    --vars /var/robotmk_local.env                # start scheduler, load env from file  (instead of env)
# ---------------------------------------------------------------------------------------------
# # SUITE CONTEXT
# robotmk                                                                        # no arg = exec suite as configured in env
# robotmk                           --vars /var/rmk/foosuiteA_8bb36c3.env  foobarsuiteA   # exec suite with env from file
# robotmk     suite    vardump         foobarsuiteA                                 # dump vars for foobarsuiteA
# ---------------------------------------------------------------------------------------------
# # SPECIALAGENT (="s.a."") CONTEXT
# robotmk                                                                        # no arg = seq & output
# (robotmk    s.a.     output)                                                   # NOT POSSIBLE - no config file
# robotmk     s.a.     output      --vars ~/var/robotmk/s.a.-hostfoo.env         # run output with env from file

# (robotmk    s.a.     sequencer)                                                # NOT POSSIBLE - no config file
# robotmk     s.a.     sequencer   --vars ~/var/robotmk/s.a.-hostfoo.env         # run requencer with env from file


def get_commands_from_pkg(pkg, root=None) -> dict:
    pkg_obj = importlib.import_module(pkg)
    pkg_path = os.path.dirname(pkg_obj.__file__)
    commands = {}
    for module in pkgutil.iter_modules([pkg_path]):
        module_obj = importlib.import_module(f"{pkg}.{module.name}")
        if module.ispkg:
            cmd_from_pkg = get_commands_from_pkg(f"{pkg}.{module.name}")
            # commands[module.name.replace("_", "-")] = cmd_from_pkg
            commands.update(cmd_from_pkg)
            # commands[module.name.replace("_", "-")] = click.Group(
            #     context_settings={"help_option_names": ["-h", "--help"]},
            #     help=module_obj.__doc__,
            #     commands=cmd_from_pkg,
            # )
            pass
            # did we get any commands?
            # commands[module.name]
        else:
            if module.name == "cli":
                # within cli.py, list all custom functions and add them as commands
                # TODO: determine the list of functions to ignore dynamically
                # cli_functions = [
                #     f
                #     for f in dir(module_obj)
                #     if (f not in ["click"]) and not f.startswith("__")
                # ]
                cli_functions = [f for f in dir(module_obj) if f == pkg.split(".")[-1]]

                for cli_function in cli_functions:
                    commands[cli_function] = getattr(module_obj, cli_function)

    return commands


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=__doc__,
    invoke_without_command=True,
    commands=get_commands_from_pkg("robotmk.context"),
)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        ctx.robotmk = Robotmk()
        ctx.robotmk.load_config(DEFAULTS)
        ctx.robotmk.run_default()
    else:
        pass


# root_commands = get_commands_from_pkg("robotmk.context")


# @click.group("robotmk", invoke_without_command=True)
# @click.pass_context
# def main(ctx):
#     print(__name__ + ": " + "(cli main)")
#     if ctx.invoked_subcommand is None:
#         print("no subcommand")
#     else:
#         pass


# @main.command()
# @click.option("--list", is_flag=True, help="List all contexts")
# def context(list):
#     if list:
#         click.echo("List all contexts")
#         click.echo("local")
#         click.echo("specialagent")
#         click.echo("suite")


# context = "local"
# robotmk = Robotmk(context)
# robotmk.load_config(DEFAULTS)
# robotmk.run()
# pass

if __name__ == "__main__":
    main()
