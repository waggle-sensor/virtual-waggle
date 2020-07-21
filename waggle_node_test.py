import unittest
import waggle_node


class TestUtils(unittest.TestCase):

    def test_build_args_from_list(self):
        r = waggle_node.get_build_args_from_list([
            'ARG1=the',
            'ARG2=colors',
            'ARG3=duke',
        ])

        self.assertEqual(r, [
            '--build-arg', 'ARG1=the',
            '--build-arg', 'ARG2=colors',
            '--build-arg', 'ARG3=duke',
        ])

    def test_build_args_from_config(self):
        r = waggle_node.get_build_args_from_dict({
            'ARG1': 'the',
            'ARG2': 'colors',
            'ARG3': 'duke',
        })

        self.assertEqual(r, [
            '--build-arg', 'ARG1=the',
            '--build-arg', 'ARG2=colors',
            '--build-arg', 'ARG3=duke',
        ])


if __name__ == '__main__':
    unittest.main()
