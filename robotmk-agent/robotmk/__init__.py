"""Robot Framework test execution and result parsing for Check_MK"""
__version__ = "0.0.37"

# from robotmk import cli
# import sys

# TODO: some bug in imports... when executed from cli, there should not be a message.

# # check if module was imported with cmdline args
# if __name__ == "robotmk" and len(sys.argv) > 1:
if __name__ == "robotmk":
    print(
        __name__
        + ": "
        + "You have imported robotmk module with sys args => execute cli!"
    )
    import robotmk.cli as cli

    cli.main()
# else:
#     print(__name__ + ": " + "You have just imported the robotmk module! No execution")
