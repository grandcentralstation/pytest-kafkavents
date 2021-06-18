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
    #name = config.getoption('name')
    #print(f"My name is: {name}")

    config.kafkaconf = {'bootstrap.servers': 'my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443', 'group.id': "foo", 'sasl.mechanism': 'PLAIN','security.protocol': 'SASL_SSL', 'sasl.username':'srvc-acct-820a23a1-b69b-48ac-b153-c3212805de0c', 'sasl.password':'baae54a6-92c1-4020-b405-935356faeb9c'}
    config.kafka_producer = Producer(config.kafkaconf)
    config.kv_session_token = secrets.token_urlsafe(16)


def pytest_runtest_setup(item):
    # print("\nconftest setting up", item)
    pass


def pytest_runtest_teardown(item):
    #print("\nconftest tearing down", item)
    pass


def pytest_report_teststatus(report, config):
    kv_session = f"{config.option.kv_sessionprefix}_{config.kv_session_token}"
    kv_topic = config.option.kv_topic

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
    #kafkavent['stdout'] = report.capstdout
    #kafkavent['stderr'] = report.capstderr
    if report.outcome == "skipped":
        kafkavent['duration'] = 0
    #if report.outcome == "failed":
    #    kafkavent['fail_message'] = report.longreprtext

    #print(f"\nKAFKAVENT ({kv_topic}) -> {kafkavent}")
    config.kafka_producer.produce('my-other-topic', json.dumps(kafkavent).rstrip())
    config.kafka_producer.flush()
    '''
    print(f"KAFKAVENT {kv_session} ({report.when}): ",
          report.nodeid, report.location,
          report.outcome, report.longrepr,
          report.duration, report.sections,
          report.keywords)
    '''