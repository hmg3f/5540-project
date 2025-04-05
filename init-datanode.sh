#!/usr/bin/env bash

#rm -rf /opt/hadoop/data/datanode/*
find /opt/hadoop/data/datanode/* ! -name 'README' -exec rm -rf {} +
chown -R hadoop:hadoop /opt/hadoop/data/datanode
chmod 755 /opt/hadoop/data/datanode
hdfs datanode
