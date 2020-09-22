import os
import subprocess
from pathlib import Path


def run(args):
    print('=== Config Info ===')
    print('Registration Key Exists:', 'Yes' if Path(
        'private/register.pem').exists() else 'No')
    print('Node ID:', os.environ.get('WAGGLE_NODE_ID'))
    print('Beehive Host:', os.environ.get('WAGGLE_BEEHIVE_HOST'))
    print()

    print('=== Playback Server Logs ===')
    subprocess.run(['docker-compose', '-p', args.project_name,
                    'logs', 'playback'])
    print()

    print('=== RabbitMQ Queue Status ===')
    subprocess.run(['docker-compose', '-p', args.project_name,
                    'exec', 'rabbitmq', 'rabbitmqctl', 'list_queues'])
    print()

    print('=== RabbitMQ Shovel Status ===')
    subprocess.run(['docker-compose', '-p', args.project_name,
                    'exec', 'rabbitmq', 'rabbitmqctl', 'eval', 'rabbit_shovel_status:status().'])
    print()


def register(subparsers):
    parser = subparsers.add_parser('report', help='show virtual waggle system report for debugging')
    parser.set_defaults(func=run)
