from pathlib import Path
import subprocess

def run(args):
    subprocess.check_call(['docker-compose', '-p', args.project_name, 'down', '--remove-orphans'])
    
    for path in ['private/key.pem', 'private/cert.pem', 'private/cacert.pem', 'private/reverse_ssh_port']:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass


def register(subparsers):
    parser = subparsers.add_parser('down', help='stop virtual waggle environment')
    parser.set_defaults(func=run)
