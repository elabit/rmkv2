from click.testing import CliRunner
import robotmk.cli.cli as cli
import re


# test help message
def test_suite_cli_help():
    """The help message shoudl contain the three contexts and the help message itself."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["suite", "--help"])
    assert result.exit_code == 0
    # assert "Robotmk CLI Interface." in result.output
    assert re.search(r"Commands:.*vardump", result.output, re.DOTALL)
