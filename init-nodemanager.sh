#!/usr/bin/env bash

sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/*.repo
sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/*.repo
sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/*.repo

yum update -y
yum install -y python3

$HADOOP_HOME/bin/yarn --config $HADOOP_CONF_DIR nodemanager
