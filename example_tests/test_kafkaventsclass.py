import pytest
import random
import sys
import time


class TestKafkavents(object):
    def test_generated(self, kvtest_outcome, kvtest_arch, kvtest_os):
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
