import click
from time import sleep
from robotmk.modes.agent import agent


@click.command(
    help="""
    Start the Robotmk Agent in background.
    The agent continuously watches the controller's state file. As soon as the state file 
    gets outdated, the agent will terminate.
    
    """
)
def bg():
    print(
        __name__ + ": " + "(cli agent): start the agent self-terminating by controller"
    )
    agent.RMKAgent(ctrl_file_controlled=True).start()


@click.command(
    help="""
    Start the Robotmk Agent in foreground.
    Used mainly for debugging purposes. The Robotmk agent won't terminate itself and run forever.
    """
)
def fg():
    print(__name__ + ": " + "(cli agent): start the agent in foreground")
    agent.RMKAgent(ctrl_file_controlled=False).start()


# @click.command(help="Stop the Robotmk Agent")
# def stop():
#     print(__name__ + ": " + "(cli agent): stop the agent")
#     agent.RMKAgent().stop()


# @click.command(help="Restart the Robotmk Agent")
# def restart():
#     print(__name__ + ": " + "(cli agent): restart the agent")
#     agent.RMKAgent().restart()
