import argparse
import os
import subprocess
import sys
import commands.up
import commands.down
import commands.report
import commands.logs
import commands.build
import commands.run
import commands.newplugin


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda args: parser.print_help())
    parser.add_argument('-p', '--project-name', default=os.path.basename(os.getcwd()), help='specify project name (default: directory name)')

    subparsers = parser.add_subparsers()
    commands.up.register(subparsers)
    commands.down.register(subparsers)
    commands.logs.register(subparsers)
    commands.report.register(subparsers)
    commands.build.register(subparsers)
    commands.run.register(subparsers)
    commands.newplugin.register(subparsers)
    args = parser.parse_args()

    try:
        args.func(args)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


if __name__ == '__main__':
    main()
