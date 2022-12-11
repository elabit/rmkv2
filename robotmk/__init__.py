# Despite of the "robotomk" executable, also make a module based call possible.
# python -m robotmk agent start
# python -m robotmk specialagent
if __name__ == "robotmk":
    import robotmk.cli as cli

    cli.main()
