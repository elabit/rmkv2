from click.testing import CliRunner
import robotmk.cli.cli as cli
import re


# test help message
def test_cli_help():
    """The help message shoudl contain the three contexts and the help message itself."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["local", "--help"])
    assert result.exit_code == 0
    # assert "Robotmk CLI Interface." in result.output
    assert re.search(r"Commands:.*output.*scheduler", result.output, re.DOTALL)
