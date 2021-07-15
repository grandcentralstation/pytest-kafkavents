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
"""PyTest plugin to send test-related events to Kafka in real-time."""
import datetime
import json
import os
import random
import re
import uuid

from confluent_kafka import Producer
#from _pytest.runner import pytest_runtest_makereport as _makereport


class KafkaProducer():
    """Produce PyTest events for Kafka."""

    def __init__(self, configfile=None, logfile=None, sessionid=None,
                 topics=None, send_events=True):
        """Manage configuring and sending events to Kafka."""
        if sessionid is None:
            session_hash = str(uuid.uuid4())
            self.session_uuid = session_hash
            if sessionid is not None:
                self.session_uuid = sessionid
            self.logfile = logfile
            self.send_events = send_events
            self.topic_packetnum = {}

        # Setup Kafka
        if self.send_events is not None:
            with open(configfile) as fileh:
                kafkaconf = json.load(fileh)

            self.producer = Producer(kafkaconf)

        self.sessionnum = 0
        for topic in topics:
            self.topic_packetnum[topic] = 0

        if logfile is not None:
            if os.path.exists(logfile):
                os.remove(logfile)

    def send(self, topics, body, type='kafkavent', header=None):
        """Send an event to Kafka."""
        self.sessionnum = self.sessionnum + 1
        # FIXME: populate topic
        # FIXME: version of schema is defined where?
        packet = {
            'header': {
                'session_id': self.session_uuid,
                'session_num': self.sessionnum,
                'topic': '',
                'packetnum': 0,
                'type': type,
                'source': 'pytest-kafkavent',
                'version': '0.01',
                'timestamp': datetime.datetime.utcnow().isoformat()
                }
            }
        packet.update({'body': body})

        # send to kafka
        if self.send_events:
            # TODO: squelch dupe topics
            for topic in topics:
                self.topic_packetnum[topic] = self.topic_packetnum[topic] + 1
                packet['header']['topic'] = topic
                packet['header']['packetnum'] = self.topic_packetnum[topic]
                self.producer.produce(topic, json.dumps(packet).rstrip())
                self.producer.flush()

        # write to file
        if self.logfile:
            #print(f'LOGFILE: {self.logfile}')
            fileh = open(self.logfile, "a")
            fileh.write(json.dumps(packet))
            fileh.write('\n')
            fileh.close()


class Kafkavents():
    """Plug in to PyTest."""

    def __init__(self, config):
        """Initialize the Kafkavents class."""
        self.config = config
        self.topics = []
        self.fail_topics = None
        self.infra_topics = None
        self.session_name = config.getoption('kv_session_name')
        self.eventlog = config.getoption('kv_eventlog', None)
        self.kafkaconfig = config.getoption('kv_configfile', None)

        if config.getoption('kv_topics'):
            self.topics = config.getoption('kv_topics').split(',')
        if config.getoption('kv_failed_topics'):
            self.failed_topics = \
                config.getoption('kv_failed_topics').split(',')
        if config.getoption('kv_infra_topics'):
            self.infra_topics = config.getoption('kv_infra_topics').split(',')
        self.all_topics = []
        if self.topics:
            self.all_topics.extend(self.topics)
        if self.failed_topics:
            self.all_topics.extend(self.failed_topics)
        if self.infra_topics:
            self.all_topics.extend(self.infra_topics)

        session_uuid = config.getoption('kv_sessionid', None)

        if self.kafkaconfig is not None:
            send_events = config.getoption('kv_sendevents')
            self.kafkaprod = KafkaProducer(self.kafkaconfig,
                                           sessionid=session_uuid,
                                           logfile=self.eventlog,
                                           send_events=send_events,
                                           topics=self.all_topics)

    @staticmethod
    def get_event_domain(nodeid):
        """Generate Kafkavents domain from PyTest nodeid."""
        nodelist = nodeid.split('::')
        filepath = nodelist[0]
        # drop the file extension
        noext_path = filepath.split('.')[0]
        domainlist = noext_path.split('/')
        # add the last nodelist elements
        offset = (len(nodelist) - 1) * -1
        domainlist.extend(nodelist[offset:])

        # check the last domtet for parametrized
        # test_generated[skipped-ARM-Linux]
        testcase_domtet = domainlist[-1:]
        ptrized = re.match('(.*)\[(.*)\]', testcase_domtet[0])
        if ptrized:
            domainlist[len(domainlist) - 1] = ptrized.groups()[0]
            domainlist.append(ptrized.groups()[1])

        # back to string
        domain = '.'.join(domainlist)

        return domain

    def pytest_sessionstart(self, session):
        """Send session start event (PyTest hook)."""
        #print('\nSESSION STARTED')
        self.kafkaprod.send(self.topics,
                            {'name': self.session_name},
                            type='sessionstart')

        if self.infra_topics is not None:
            self.kafkaprod.send(self.infra_topics,
                                {'function': 'pytest_sessionfinish'},
                                type='infra')
            # TODO: design the schema

    def pytest_sessionfinish(self, session, exitstatus):
        """Send session finished event (PyTest hook)."""
        #print('\nSESSION FINISHED')
        self.kafkaprod.send(self.topics,
                            {'name': self.session_name},
                            type='sessionend')

        if self.infra_topics is not None:
            self.kafkaprod.send(self.infra_topics,
                                {'function': 'pytest_sessionfinish'},
                                type='infra')
            # TODO: design the schema

    def pytest_runtest_logreport(self, report):
        """Get the results of a testcase (PyTest hook)."""
        #print('RUNTEST LOGREPORT ', report.nodeid)
        event_topics = self.topics.copy()

        if report.when == 'teardown':
            return
        if report.when == 'setup' and report.outcome != 'skipped':
            return

        kafkavent = {}
        kafkavent['pytest_when'] = report.when
        kafkavent['nodeid'] = report.nodeid
        kafkavent['domain'] = self.get_event_domain(report.nodeid)
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

        if self.infra_topics is not None:
            self.kafkaprod.send(self.infra_topics,
                                {'function': 'pytest_runtest_logreport'},
                                type='infra')
            # TODO: design the schema

    def pytest_runtest_setup(self, item):
        """Capture event info from test setup (PyTest hook)."""
        # print("\nconftest setting up", item)
        if self.infra_topics is not None:
            self.kafkaprod.send(self.infra_topics,
                                {'function': 'pytest_runtest_setup'},
                                type='infra')
            # TODO: design the schema

    def pytest_runtest_teardown(self, item):
        """Capture event info from test teardown (PyTest hook)."""
        #print("\nconftest tearing down", item)
        if self.infra_topics is not None:
            self.kafkaprod.send(self.infra_topics,
                                {'function': 'pytest_runtest_teardown'},
                                type='infra')
            # TODO: design the schema

    def pytest_terminal_summary(self, terminalreporter, exitstatus):
        """Capture summary at the end of tests (PyTest hook)."""
        kafkavent = {}
        kafkavent['passed'] = len(terminalreporter.stats.get('passed', []))
        kafkavent['failed'] = len(terminalreporter.stats.get('failed', []))
        kafkavent['skipped'] = len(terminalreporter.stats.get('skipped', []))
        kafkavent['xfailed'] = len(terminalreporter.stats.get('xfailed', []))
        kafkavent['status'] = exitstatus
        self.kafkaprod.send(self.topics, kafkavent, type='summary')

        if self.infra_topics is not None:
            self.kafkaprod.send(self.infra_topics,
                                {'function': 'pytest_terminal_summary'},
                                type='infra')
            # TODO: design the schema

    def pytest_generate_tests(self, metafunc):
        """Generate tests to test event creation (PyTest hook)."""
        if metafunc.config.getoption("kv_test"):
            nums = metafunc.config.getoption('kv_test').split(',')
            pass_num = int(nums[0])
            fail_num = int(nums[1])
            skip_num = int(nums[2])
            xfail_num = int(nums[3])

            print(f'Automatically generating tests w/ '
                  f'{pass_num} passes '
                  f'{fail_num} fails '
                  f'{skip_num} skips '
                  f'{xfail_num} xfails')

            test_outcomes = ['passed' for i in range(pass_num)]
            test_outcomes.extend(['failed' for i in range(fail_num)])
            test_outcomes.extend(['skipped' for i in range(skip_num)])
            test_outcomes.extend(['xfailed' for i in range(xfail_num)])

            random.shuffle(test_outcomes)

            if "kvtest_outcome" in metafunc.fixturenames:
                metafunc.parametrize("kvtest_outcome", test_outcomes)
            if "kvtest_arch" in metafunc.fixturenames:
                metafunc.parametrize("kvtest_arch", ['x86_64', 'ARM'])
            if "kvtest_os" in metafunc.fixturenames:
                metafunc.parametrize("kvtest_os", ['Linux', 'MacOS'])


def pytest_addoption(parser):
    """Add command-line options."""
    group = parser.getgroup("kafkavents")
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
        help='Kafka topic(s) to send events on',
    )
    group.addoption(
        "--kv-topics-failed",
        action="store",
        dest="kv_failed_topics",
        default=None,
        help='Kafka topic(s) to send FAILED test events on',
    )
    group.addoption(
        "--kv-topics-infra",
        action="store",
        dest="kv_infra_topics",
        default=None,
        help='Kafka topic(s) to send PyTest infrastructure events on',
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
    group.addoption(
        "--kv-skipsend",
        action="store_false",
        dest="kv_sendevents",
        default=True,
        help='Skip sending events',
    )
    # FIXME: solidify option names


def pytest_configure(config):
    """Configure global items and add things to the config (PyTest hook)."""
    if config.getoption('kv_configfile', None):
        print('pytest-kafkavents')
        kafkavents = Kafkavents(config)
        #config.pluginmanager.register(kafkavent, 'kafkavent')
        config.pluginmanager.register(kafkavents)



def pytest_unconfigure(config):
    """Unconfigure the items configured in configure (PyTest hook)."""
    pass
    # FIXME: actually unconfigure things

'''
def pytest_runtest_makereport(item, call):
    print('\nRUNTEST MAKEREPORT')
    #print(item.config)
'''
