#!/bin/bash
# Build + chay MapReduce job PopularityByYear trong container namenode
# Yeu cau: file /tmp/ratings.csv da copy vao container (docker cp)
# Chay:  docker exec namenode bash /tmp/run_mr.sh
set -e
export HADOOP_HOME=/opt/hadoop-3.2.1
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HADOOP_CLASSPATH=$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*
export HADOOP_MAPRED_HOME=$HADOOP_HOME/share/hadoop/mapreduce

echo "=== 1. Tao file input CSV tren HDFS ==="
hdfs dfs -rm -r -f /recsys/ratings_csv >/dev/null 2>&1 || true
hdfs dfs -mkdir -p /recsys/ratings_csv
if [ ! -f /tmp/ratings.csv ]; then
  echo "ERROR: thieu /tmp/ratings.csv trong container."
  echo "  docker cp D:\\recsys_data\\raw\\ml-25m\\ratings.csv namenode:/tmp/ratings.csv"
  exit 3
fi
hdfs dfs -put -f /tmp/ratings.csv /recsys/ratings_csv/part-00000.csv
hdfs dfs -ls -h /recsys/ratings_csv

echo "=== 2. Bien dich Java ==="
mkdir -p /tmp/mrbuild
cd /tmp/mrbuild
javac -cp "$HADOOP_CLASSPATH" -d . /tmp/PopularityByYear.java
jar cf popularity.jar PopularityByYear*.class

echo "=== 3. Chay MapReduce ==="
hdfs dfs -rm -r -f /recsys/out/popularity_by_year >/dev/null 2>&1 || true
hadoop jar /tmp/mrbuild/popularity.jar PopularityByYear \
  /recsys/ratings_csv /recsys/out/popularity_by_year

echo "=== 4. Ket qua ==="
hdfs dfs -ls -h /recsys/out/popularity_by_year
echo "--- 5 dong dau ---"
hdfs dfs -cat /recsys/out/popularity_by_year/part-r-00000 2>/dev/null | head -5 || true
echo "--- tong so dong ---"
hdfs dfs -cat /recsys/out/popularity_by_year/part-r-00000 2>/dev/null | wc -l
