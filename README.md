# pytest-kafkavents


Create a Kafka instance on [Red Hat OpenShift Streams for Apache Kafka](https://developers.redhat.com/products/red-hat-openshift-streams-for-apache-kafka/getting-started)

Install Kafka client package

Copy and configure app-services.properties

Create topics (with the client command)

Start one consumer in one window

    $ ./kafka-console-consumer.sh --bootstrap-server my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443 --consumer.config ../config/app-services.properties --from-beginning --topic my-other-topic

Start another consumer in another window

    $ ./kafka-console-consumer.sh --bootstrap-server my-kafka-n--u-bvmxxe-dvgycp-axfjmaftyk.bf2.kafka.rhcloud.com:443 --consumer.config ../config/app-services.properties --from-beginning --topic my-other-topic-test


Clone me

Install plugin for dev

    $ pip install -e .

Run pytest

    $ pytest example_tests/ --junitxml=/tmp/kafkavent.xml --kv_topics=my-other-topic
    $ pytest example_tests/ -q --kv_topics my-other-topic --kv_topics_failed my-other-topic-test --kv_conf examples/kafka_conf.json

TODO: just create a container with all of this goodness in it.