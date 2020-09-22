import sys


def notice(msg):
    print(f'\033[94mNOTICE: {msg}\033[00m', file=sys.stderr)


def warning(msg):
    print(f'\033[93mWARNING: {msg}\033[00m', file=sys.stderr)


def fatal(msg):
    print(f'\033[91mERROR: {msg}\033[00m', file=sys.stderr)
    sys.exit(1)
