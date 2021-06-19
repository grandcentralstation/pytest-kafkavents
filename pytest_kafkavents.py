# Copyright 2021 Jonathan Holloway <loadtheaccumulator@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software. If not, see <http://www.gnu.org/licenses/>.
#
import json
import os
import pytest
import random
import uuid

from confluent_kafka import Producer


'''
def pytest_runtest_setup(item):
    # print("\nconftest setting up", item)
    pass


def pytest_runtest_teardown(item):
    #print("\nconftest tearing down", item)
    pass


def pytest_runtest_makereport(item, call):
    print('\nRUNTEST MAKEREPORT')
    #print(item.config)
'''

class KafkaProducer(object):
    def __init__(self, configfile=None, logfile=None, sessionid=None):
        if sessionid is None:
            session_hash = str(uuid.uuid4())
            self.session_uuid = session_hash
            self.logfile = logfile

        # Setup Kafka
        fileh = open(configfile)
        kafkaconf = json.load(fileh)
        fileh.close()

        self.producer = Producer(kafkaconf)

        self.packetnum = 0

        if os.path.exists(logfile):
            os.remove(logfile)

    def send(self, topics, event, type='kafkavent', header=None):
        self.packetnum = self.packetnum + 1
        packet = {
            'header': {
                'session_id': self.session_uuid,
                'packetnum': self.packetnum,
                'type': type,
                'source': 'pytest-kafkavent',
                'version': '0.01'
                }
            }
        packet.update({'event': event})

        # send to kafka
        for topic in topics:
            self.producer.produce(topic, json.dumps(packet).rstrip())
            self.producer.flush()

        # write to file
        if self.logfile:
            fileh = open(self.logfile, "a")
            fileh.write(json.dumps(packet))
            fileh.write('\n')
            fileh.close()

class Kafkavent(object):
    def __init__(self, config):
        self.config = config
        self.topics = []
        self.fail_topics = None
        self.session_name = config.getoption('kv_session_name')
        self.eventlog = config.getoption('kv_eventlog', None)
        self.kafkaconfig = config.getoption('kv_configfile', None)

        if config.getoption('kv_topics'):
            self.topics = config.getoption('kv_topics').split(',')
        if config.getoption('kv_failed_topics'):
            self.failed_topics = config.getoption('kv_failed_topics').split(',')

        session_uuid = config.getoption('kv_sessionid', None)

        if self.kafkaconfig is not None:
            self.kafkaprod = KafkaProducer(self.kafkaconfig,
                                           sessionid=session_uuid, logfile=self.eventlog)

    def pytest_sessionstart(self, session):
        #print('\nSESSION STARTED')
        self.kafkaprod.send(self.topics, {'name': self.session_name}, type='sessionstart')

    def pytest_sessionfinish(self, session, exitstatus):
        #print('\nSESSION FINISHED')
        self.kafkaprod.send(self.topics, {'name': self.session_name}, type='sessionend')

    def pytest_runtest_logreport(self, report):
        #print('RUNTEST LOGREPORT ', report.nodeid)
        event_topics = self.topics.copy()

        if report.when == 'teardown':
            return
        if report.when == 'setup' and report.outcome != 'skipped':
            return

        kafkavent = {}
        kafkavent['pytest_when'] = report.when
        kafkavent['nodeid'] = report.nodeid
        kafkavent['status'] = report.outcome
        # TODO: add timestamp
        kafkavent['duration'] = report.duration
        if report.capstdout:
            kafkavent['stdout'] = report.capstdout
        if report.capstderr:
            kafkavent['stderr'] = report.capstderr
        if report.outcome == "skipped":
            kafkavent['duration'] = 0
        if report.outcome == "failed":
            kafkavent['message'] = report.longreprtext
            if self.failed_topics is not None:
                event_topics.extend(self.failed_topics)

        self.kafkaprod.send(event_topics, kafkavent, type='testresult')

    def pytest_terminal_summary(self, terminalreporter, exitstatus):
        kafkavent = {}
        kafkavent['passed'] = len(terminalreporter.stats.get('passed',[]))
        kafkavent['failed'] = len(terminalreporter.stats.get('failed',[]))
        kafkavent['skipped'] = len(terminalreporter.stats.get('skipped',[]))
        kafkavent['xfailed'] = len(terminalreporter.stats.get('xfailed',[]))
        kafkavent['status'] = exitstatus
        self.kafkaprod.send(self.topics, kafkavent, type='summary')

    def pytest_generate_tests(self, metafunc):
        print('PYTEST GENERATE TESTS')
        if metafunc.config.getoption("kv_test"):
            nums = metafunc.config.getoption('kv_test').split(',')
            pass_num = int(nums[0])
            fail_num = int(nums[1])
            skip_num = int(nums[2])
            xfail_num = int(nums[3])
            pass_num = pass_num - fail_num - skip_num - xfail_num

            test_outcomes = ['passed' for i in range(pass_num)]
            test_outcomes.extend(['failed' for i in range(fail_num)])
            test_outcomes.extend(['skipped' for i in range(skip_num)])
            test_outcomes.extend(['xfailed' for i in range(xfail_num)])

            random.shuffle(test_outcomes)

            if "kvtest_outcome" in metafunc.fixturenames:
                metafunc.parametrize("kvtest_outcome", test_outcomes)

def pytest_addoption(parser):
    group = parser.getgroup("kafkavent")
    group.addoption(
        "--kv-conf",
        action="store",
        dest="kv_configfile",
        default=None,
        help='Kafka connection configs',
    )
    group.addoption(
        "--kv-sessionname",
        action="store",
        dest="kv_session_name",
        default="Kafkavent Session",
        help='Session name for endpoint consumers to collate session data',
    )
    group.addoption(
        "--kv-sessionid",
        action="store",
        dest="kv_session_id",
        default=None,
        help='Session ID for endpoint consumers to collate session data',
    )
    group.addoption(
        "--kv-topics",
        action="store",
        dest="kv_topics",
        default=[],
        help='Kafka topic to send events on',
    )
    group.addoption(
        "--kv-topics-failed",
        action="store",
        dest="kv_failed_topics",
        default=None,
        help='Kafka topic to send FAILED test events on',
    )
    group.addoption(
        "--kv-eventlog",
        action="store",
        dest="kv_eventlog",
        default=None,
        help='Log to store events for debug and replay',
    )
    group.addoption(
        "--kv-test",
        action="store",
        dest="kv_test",
        default=None,
        help='Generate test events (# passes,# fails,# skips,# xfails)',
    )


def pytest_configure(config):
    """Configure global items and add things to the config"""

    kafkavent = Kafkavent(config)
    config.pluginmanager.register(kafkavent, 'kafkavent')


def pytest_unconfigure(config):
    pass
