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
        "--kv_topic",
        action="store",
        dest="kv_topic",
        default="kafkavent_realtime",
        help='Kafka topic to send events on',
    )


def pytest_configure(config):
    """Configure global items and add things to the config"""
    kv_configfile = config.getoption('kv_configfile')

    # Setup Kafka
    fileh = open(kv_configfile)
    kafkaconf = json.load(fileh)
    fileh.close()

    config.kafka_producer = Producer(kafkaconf)
    config.kv_session_token = secrets.token_urlsafe(16)


def pytest_unconfigure(config):
    pass


def pytest_runtest_setup(item):
    # print("\nconftest setting up", item)
    pass


def pytest_runtest_teardown(item):
    #print("\nconftest tearing down", item)
    pass


def pytest_sessionstart():
    print('\nSESSION STARTED')


def pytest_sessionfinish():
    print('\nSESSION FINISHED')


def pytest_report_teststatus(report, config):
    kv_session = f"{config.option.kv_sessionprefix}_{config.kv_session_token}"
    kv_topics = config.option.kv_topic.split(',')

    if report.when == 'teardown':
        return
    if report.when == 'setup' and report.outcome != 'skipped':
        return

    kafkavent = {}
    kafkavent['session'] = kv_session
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

    #print(f"\nKAFKAVENT ({kv_topic}) -> {kafkavent}")
    for topic in kv_topics:
        config.kafka_producer.produce(topic, json.dumps(kafkavent).rstrip())
        config.kafka_producer.flush()
    '''
    print(f"KAFKAVENT {kv_session} ({report.when}): ",
          report.nodeid, report.location,
          report.outcome, report.longrepr,
          report.duration, report.sections,
          report.keywords)
    '''
