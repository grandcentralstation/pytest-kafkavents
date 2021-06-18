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
import pytest
import secrets

from confluent_kafka import Producer


def pytest_addoption(parser):
    group = parser.getgroup("kafkavent")
    group.addoption(
        "--kv_conf",
        action="store",
        dest="kv_configfile",
        default="kafka_conf.json",
        help='Kafka connection configs',
    )
    group.addoption(
        "--kv_sessionprefix",
        action="store",
        dest="kv_sessionprefix",
        default="1234567890",
        help='Session ID for endpoint consumers to collate session data',
    )
    group.addoption(
        "--kv_topics",
        action="store",
        dest="kv_topics",
        default=[],
        help='Kafka topic to send events on',
    )
    group.addoption(
        "--kv_topics_fail",
        action="store",
        dest="kv_fail_topics",
        default=None,
        help='Kafka topic to send FAILED test events on',
    )
    group.addoption(
        "--kv_topics_pass",
        action="store",
        dest="kv_pass_topics",
        default=None,
        help='Kafka topic to send PASSED test events on',
    )


def pytest_configure(config):
    """Configure global items and add things to the config"""
    kv_configfile = config.getoption('kv_configfile')

    '''
    # Setup Kafka
    fileh = open(kv_configfile)
    kafkaconf = json.load(fileh)
    fileh.close()

    config.kafka_producer = Producer(kafkaconf)
    config.kv_session_token = secrets.token_urlsafe(16)
    '''

    kafkavent = Kafkavent(config)
    config.pluginmanager.register(kafkavent, 'kafkavent')


def pytest_unconfigure(config):
    pass


def pytest_runtest_setup(item):
    # print("\nconftest setting up", item)
    pass


def pytest_runtest_teardown(item):
    #print("\nconftest tearing down", item)
    pass


def pytest_sessionstart(session):
    print('\nSESSION STARTED')


def pytest_sessionfinish(session, exitstatus):
    print('\nSESSION FINISHED')


def pytest_terminal_summary(terminalreporter):
    print('\nTERMINAL SUMMARY')


def pytest_runtest_makereport(item, call):
    print('\nRUNTEST MAKEREPORT')
    print(item.config)


class KafkaProducer(object):
    def __init__(self, configfile, sessionid=None):
        if sessionid is None:
            session_hash = secrets.token_urlsafe(16)
            self.session_uuid = session_hash

        # Setup Kafka
        fileh = open(configfile)
        kafkaconf = json.load(fileh)
        fileh.close()

        self.producer = Producer(kafkaconf)

    def send(self, topics, event, header=None):
        print(topics)
        header = {
            'header': {
                'source': 'pytest-kafkavent',
                'version': '0.01',
                'session_id': self.session_uuid
                }
            }
        packet = header.update({'event': event})

        for topic in topics:
            print(topic)
            self.producer.produce(topic, json.dumps(header).rstrip())
            self.producer.flush()


class Kafkavent(object):
    def __init__(self, config):
        self.config = config
        self.topics = []
        self.fail_topics = None

        if config.getoption('kv_topics'):
            self.topics = config.getoption('kv_topics').split(',')
        if config.getoption('kv_fail_topics'):
            self.fail_topics = config.getoption('kv_fail_topics').split(',')

        session_uuid = config.getoption('kv_sessionid', None)

        self.kafkaprod = KafkaProducer(config.getoption('kv_configfile'),
                                       sessionid=session_uuid)

    def pytest_runtest_logreport(self, report):
        print('RUNTEST LOGREPORT ', report.nodeid)
        print(self.config)

    def pytest_report_teststatus(self, report, config):
        print('REPORT TESTSTATUS')

        event_topics = self.topics.copy()

        if report.when == 'teardown':
            return
        if report.when == 'setup' and report.outcome != 'skipped':
            return

        kafkavent = {}
        kafkavent['pytest_when'] = report.when
        kafkavent['nodeid'] = report.nodeid
        kafkavent['status'] = report.outcome
        kafkavent['duration'] = report.duration
        if report.capstdout:
            kafkavent['stdout'] = report.capstdout
        if report.capstderr:
            kafkavent['stderr'] = report.capstderr
        if report.outcome == "skipped":
            kafkavent['duration'] = 0
        if report.outcome == "failed":
            kafkavent['message'] = report.longreprtext
            if self.fail_topics is not None:
                event_topics.extend(self.fail_topics)

        self.kafkaprod.send(event_topics, kafkavent)

        '''
        print(f"KAFKAVENT {kv_session} ({report.when}): ",
            report.nodeid, report.location,
            report.outcome, report.longrepr,
            report.duration, report.sections,
            report.keywords)
        '''
