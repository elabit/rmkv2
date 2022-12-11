import click

# from robotmk_agent import RMKAgent


def main():
    print("(cli agent) main function")
    pass


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


if __name__ == "__main__":
    main()
