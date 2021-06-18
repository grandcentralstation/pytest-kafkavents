# pytest-kafkavents


clone me
Install plugin for dev

    $ pip install -e .

Run the test pytest

    $ pytest example_tests \
      --junitxml=/tmp/kafkavent.xml --kv_sessionprefix=holloway \
      --kv_topic=my-other-topic --no-summary

