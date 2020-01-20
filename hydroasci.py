
def cli_description():
    try:
        import textwrap
        return textwrap.dedent('''\
         _    _           _                       _       _
        | |  | |         | |                     | |     | |
        | |__| |_   _  __| |_ __ ___  _ __   ___ | | __ _| |_ ___  _ __
        |  __  | | | |/ _` | '__/ _ \| '_ \ / _ \| |/ _` | __/ _ \| '__|
        | |  | | |_| | (_| | | | (_) | |_) | (_) | | (_| | || (_) | |
        |_|  |_|\__, |\__,_|_|  \___/| .__/ \___/|_|\__,_|\__\___/|_|
                 __/ |               | |
                |___/                |_|
        for interacting with hydrographic depth measurements
        to create safe navigational isobaths.
        ----------------------------------------------------
        ''')
    except:
        return 'HydroPolator: for interacting with hydrographic depth measurements to create safe navigational isobaths.'
