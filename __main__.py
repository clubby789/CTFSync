import os


def main():
    from . import server
    os.chdir(os.path.dirname(os.path.abspath(__file__))) 
    server.start_notes()


if __name__ == "__main__":
    main()
