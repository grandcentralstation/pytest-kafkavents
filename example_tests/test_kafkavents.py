import pytest
import random
import sys
import time


def test_generated(kvtest_outcome):
    #time.sleep(random.randint(0, 1))

    if kvtest_outcome == "passed":
        assert 1 == 1

    if kvtest_outcome == "failed":
        print("stdout yada yada")
        print("stderr yada yada", file=sys.stderr)
        assert 1 == 2
    # TODO: generate some lorem ipsum on stdout and stderr for fails

    if kvtest_outcome == "skipped":
        pytest.skip('intentionally skipped')

    if kvtest_outcome == "xfailed":
        pytest.xfail('intentionally failed')
