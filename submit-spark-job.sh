#!/usr/bin/env bash

echo 'Spark: Installing python dependencies'
pip install contractions num2words nltk pandas pyarrow

echo "Waiting for HDFS to leave safe mode..."

while true; do
  SAFE_MODE=$(hdfs dfsadmin -safemode get | grep 'Safe mode is ON')
  if [ -z "$SAFE_MODE" ]; then
    echo "HDFS is out of safe mode."
    break
  fi
  sleep 5
done

echo 'Spark: Waiting to submit job...'
sleep 5
echo 'Spark: Submitting job'

# /opt/spark/bin/spark-submit \
#   --master yarn \
#   --deploy-mode client \
#   /opt/spark/jobs/tweets.py
