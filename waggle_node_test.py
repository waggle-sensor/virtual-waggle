import argparse
import unittest
import json
import commands.build


class TestUtils(unittest.TestCase):

    def test_valid_config(self):
        commands.build.raise_for_invalid_config({
            'id': 123,
            'version': '1.2.3',
            'name': 'test',
        })

        with self.assertRaises(KeyError):
            commands.build.raise_for_invalid_config({
                'version': '1.2.3',
                'name': 'test',
            })

        with self.assertRaises(ValueError):
            commands.build.raise_for_invalid_config({
                'id': '123',
                'version': 1,
                'name': 'test',
            })

    def test_image_name_for_config(self):
        name = commands.build.get_image_name_for_config({
            'id': 123,
            'name': 'test',
            'version': '1.2.3',
        })

        self.assertEqual(name, 'plugin-test:1.2.3')


if __name__ == '__main__':
    unittest.main()
