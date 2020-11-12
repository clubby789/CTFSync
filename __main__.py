import os


def main(port=8080, oauth=False):
    from . import server
    server.start_notes(port=port)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    import configparser
    config = configparser.ConfigParser()
    config.read('conf.ini')
    main(config.getint('MISC', 'port'), config.getboolean('OAUTH', 'enabled'))
