import argparse
import unittest
import waggle_node


class TestUtils(unittest.TestCase):

    def test_valid_config(self):
        waggle_node.raise_for_invalid_config({
            'id': 123,
            'version': '1.2.3',
            'name': 'test',
        })

        with self.assertRaises(KeyError):
            waggle_node.raise_for_invalid_config({
                'version': '1.2.3',
                'name': 'test',
            })

        with self.assertRaises(ValueError):
            waggle_node.raise_for_invalid_config({
                'id': '123',
                'version': 1,
                'name': 'test',
            })

    def test_build_config(self):
        args = argparse.Namespace(plugin_dir='/path/to/plugin', build_arg=[])

        cmd = waggle_node.get_build_command_for_config(args, {
            'id': 123,
            'name': 'test',
            'version': '1.2.3',
            'sources':
            [
                {
                    'name': 'default',  # optional, default: 'default'
                    # required
                    'architectures': ['linux/amd64', 'linux/arm/v7', 'linux/arm/v8'],
                    'url': 'https://github.com/waggle-sensor/edge-plugins.git',  # required
                    'branch': 'master',  # optional, default: master
                    'directory': 'plugin-simple',  # optional, default: root of git repository
                    # optional, default: Dockerfile , relative to context directory
                    'dockerfile': 'Dockerfile_sage',
                    'build_args': {
                        'K1': 'V1',
                        'K2': 'V2',
                        'K3': 'V3',
                    }
                },
            ]
        })

        self.assertEqual(cmd, [
            'docker', 'build',
            '--build-arg', 'K1=V1',
            '--build-arg', 'K2=V2',
            '--build-arg', 'K3=V3',
            '--label', 'waggle.plugin.id=123',
            '--label', 'waggle.plugin.version=1.2.3',
            '--label', 'waggle.plugin.name=test',
            '-t', 'plugin-test:1.2.3',
            '/path/to/plugin'])

    def test_image_name_for_config(self):
        name = waggle_node.get_image_name_for_config({
            'id': 123,
            'name': 'test',
            'version': '1.2.3',
        })

        self.assertEqual(name, 'plugin-test:1.2.3')


if __name__ == '__main__':
    unittest.main()
