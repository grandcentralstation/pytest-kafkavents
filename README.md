# pytest-kafkavents

PyTest Kafkavents is a plugin for real time streaming of test result events to a Kafka instance.
Events can also be logged for batch replay of events via another utility (in the works).

## Steps to use pytest-kafkavents

1. Clone me (soon to be pip install me)

```
    git clone https://github.com/grandcentralstation/pytest-kafkavents.git
```
To install for dev
```
    pip install -e .
```

2. Create a Kafka instance on [Red Hat OpenShift Streams for Apache Kafka](https://developers.redhat.com/products/red-hat-openshift-streams-for-apache-kafka/getting-started)

3. Download and install the client from the [Apache Kafka client](https://kafka.apache.org/downloads) website.

**SIDENOTE:** Pytest-Kafkavent uses the Confluent Python Kafka library

On Fedora...

    dnf info python3-confluent-kafka
    pip show confluent-kafka

4. Copy and configure app-services.properties template to your local kafka client bin directory and fill-in info for your instance.

5. Create topics (with the client command)
```
./kafka-topics.sh --create --topic kafkavent --bootstrap-server my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443 --command-config ../config/app-services.properties
./kafka-topics.sh --create --topic kafkavent-failed --bootstrap-server my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443 --command-config ../config/app-services.properties
```

6. Start one consumer in one window to see pytest-kafkavent messages for all tests
```
    ./kafka-console-consumer.sh --bootstrap-server my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443 \
    --consumer.config ../config/app-services.properties --from-beginning --topic kafkavent
```
7. Start another consumer in another window to see pytest-kafkavent messages for failed tests only
```
    ./kafka-console-consumer.sh --bootstrap-server my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443 \
    --consumer.config ../config/app-services.properties --from-beginning --topic kafkavent-failed
```
9. Run the example pytest test scripts
```
    pytest example_tests/ --junitxml=/tmp/kafkavent.xml --kv-topics my-other-topic
    pytest example_tests/ -q --kv-conf examples/kafka_conf.json \
    --kv-topics kafkavent --kv-topics-failed kafkavent-failed 
```
10. Or just pull the container from [Quay.io](https://quay.io) :-)

TODO: create a container with all of this goodness in it, upload to Quay.io, and link here
