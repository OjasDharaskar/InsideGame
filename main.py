"""
Inside: The Watchtower Silo
Main Game Entry Point
"""

from core.engine import Engine


def main():
    engine = Engine(width=1280, height=720)
    engine.run()


if __name__ == "__main__":
    main()
