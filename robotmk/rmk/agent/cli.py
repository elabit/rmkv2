import click
from robotmk.rmk.agent import agent


@click.command(help="Start the Robotmk Agent daemon")
def start():
    print("(cli agent): start the daemon")
    # agent = RMKAgent()
    # agent.start()


@click.command(help="Stop the Robotmk Agent daemon")
def stop():
    print("(cli agent): stop the daemon")


@click.command(help="Restart the Robotmk Agent daemon")
def restart():
    print("(cli agent): restart the daemon")
