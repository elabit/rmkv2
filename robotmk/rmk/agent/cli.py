import click
from time import sleep
from robotmk.rmk.agent import agent


@click.command(help="Start the Robotmk Agent daemon")
def start():
    print(__name__ + ": " + "(cli agent): start the daemon")
    agent.Daemon().start()


@click.command(help="Stop the Robotmk Agent daemon")
def stop():
    print(__name__ + ": " + "(cli agent): stop the daemonX")
    agent.Daemon().stop()


@click.command(help="Restart the Robotmk Agent daemon")
def restart():
    print(__name__ + ": " + "(cli agent): restart the daemon")
    agent.Daemon().restart()
