import os


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from . import server
    server.start_notes()
