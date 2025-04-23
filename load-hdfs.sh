#!/usr/bin/env bash

echo "[loader] Waiting for HDFS to be ready..."

# Wait for NameNode web UI to respond (optional, but helpful)
until curl -s http://namenode:9870 > /dev/null; do
  echo "[loader] Waiting for NameNode Web UI at http://namenode:9870..."
  sleep 5
done

# Try HDFS until it's ready
for i in {1..10}; do
    hdfs dfs -mkdir -p /data && break
    echo "[loader] HDFS not ready yet, retrying ($i)..."
    sleep 5
done

# Disable safe mode
hdfs dfsadmin -safemode leave

echo "[loader] Putting files into HDFS..."
hdfs dfs -put -f /data/* /data/

echo "[loader] Done. Listing contents:"
hdfs dfs -ls /data
