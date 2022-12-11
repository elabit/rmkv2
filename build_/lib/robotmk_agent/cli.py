import argparse
from robotmk_agent import agent_main


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", help="Execution mode (agent|specialagent|robot)")
    # TODO: only in mode robot
    parser.add_argument("suite", help="Path to the suite to run (mode: robot)")
    args = parser.parse_args()
    agent_main(args.mode, args.suite)

if __name__ == "__main__":
    main()