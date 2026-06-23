import sys

import pytest

from src.cli import main


class TestCli:
    def test_no_args_prints_usage(self):
        testargs = ["api-tester"]
        with pytest.raises(SystemExit):
            sys.argv = testargs
            main()

    def test_nonexistent_file(self):
        testargs = ["api-tester", "nonexistent.yaml"]
        with pytest.raises(SystemExit):
            sys.argv = testargs
            main()

    def test_invalid_var_format(self):
        testargs = ["api-tester", "test.yaml", "--var", "INVALID"]
        with pytest.raises(SystemExit):
            sys.argv = testargs
            main()
