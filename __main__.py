import os


def main(port):
    from . import server
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server.start_notes(port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Launch a CTFSync server')
    parser.add_argument('--port', metavar='port', type=int, const=8080,
                        nargs='?', help='Port to launch on')
    args = parser.parse_args()
    main(args.port)
