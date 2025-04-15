#!/usr/bin/env bash

/opt/kafka/bin/kafka-topics.sh --create --topic social_media --partitions 1 --replication-factor 1 --bootstrap-server broker-1:19092
/opt/kafka/bin/kafka-topics.sh --create --topic openkc_data --partitions 1 --replication-factor 1 --bootstrap-server broker-1:19092
/opt/kafka/bin/kafka-topics.sh --create --topic shot_spotter --partitions 1 --replication-factor 1 --bootstrap-server broker-1:19092
