#!/usr/bin/env python

### Imports
import re
import contractions
import nltk
import pyarrow
import html

import pandas as pd

from num2words import num2words
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp, hour, col, when, rand, floor, pandas_udf
from pyspark.sql.types import StringType

nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('universal_tagset')

### Spark Configuration
# create the spark session
spark = SparkSession.builder \
    .appName("SocialMediaProcessor") \
    .getOrCreate()

spark.conf.set("spark.sql.repl.eagerEval.enabled", True)
spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")

### Import Data
df = spark.read.csv('hdfs://namenode:9000/data/tweets.csv', header=True, inferSchema=True)
df_orig = df

### Preprocessing
## Dataframe Preprocessing
df = df.drop('flag')

# parse dates
datetime_string = "EEE MMM dd HH:mm:ss z yyyy"
df = df.withColumn('Date', to_timestamp(df.Date, datetime_string))
# df = df.withColumn('Day', weekday(df.Date))
df = df.withColumn('Hour', hour(df.Date))

df = df.withColumnRenamed('Target', 'Positive')
df = df.withColumn('Positive', when(col('Positive') == 4, 1).otherwise(0))

# tag texts that appear to be related to crime
crime_keywords = ['murder', 'murderer', 'theft', 'assault', 'robbery', 'stole', 'steal', 'stealing', 'burglary', 'arrest', 'arson', 'drug', 'drugs', 'police', 'suspect', 'violence']

df = df.withColumn(
    'crime_related',
    when(col('Text').rlike("(?i)\\b(" + "|".join(crime_keywords) + ")\\b"), 1).otherwise(0)
)

df.groupBy('crime_related').count().show()

df_crime = df.filter(col('crime_related')==1)
df_crime.select('Text').show(5, truncate=False)

# generate example zip codes
df = df.withColumn("Zip", floor(rand() * 70).cast("int"))

# handle class imbalance
count_0 = df.filter(df.crime_related == 0).count()
count_1 = df.filter(df.crime_related == 1).count()

class_ratio = count_1 / count_0

df_0 = df.filter(df.crime_related == 0).sample(withReplacement=False, fraction=class_ratio, seed=42)
df_1 = df.filter(df.crime_related == 1)

df_balanced = df_0.union(df_1)

# shuffle rows
df_balanced = df_balanced.orderBy(rand())

df_balanced.show()

## Text Preprocessing
acronyms = {
    "mr.": "mister", "mrs.": "misses", "dr.": "doctor", "st.": "street",
    "u.s.": "united states", "e.g.": "for example", "i.e.": "that is",
    "vs.": "versus", "w/": "with", "w/o": "without", "n/a": "not applicable",
    "thx": "thanks", "u": "you", "wut": "what", "wtf": "what the fuck",
    "idk": "i do not know", "luv": "love", "irl": "in real life"
}
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# preprocessing functions
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return 'a'
    elif treebank_tag.startswith('V'):
        return 'v'
    elif treebank_tag.startswith('N'):
        return 'n'
    elif treebank_tag.startswith('R'):
        return 'r'
    else:
        return None

def expand_contractions_and_acronyms(text):
    text = contractions.fix(text)
    pattern = re.compile(r'\b(' + '|'.join(acronyms.keys()) + r')\b', re.IGNORECASE)
    text = pattern.sub(lambda m: acronyms.get(m.group(0).lower(), m.group(0)), text)
    return text

def handle_web_elements(text):
    text = re.sub(r'@[\w_]+', '<user>', text)
    text = re.sub(r'#[\w_]+', '<hashtag>', text)
    text = re.sub(r'\$', ' dollar ', text)
    text = re.sub(r'€', ' euro ', text)
    text = re.sub(r'http\S+', 'URL', text)
    return text

def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)

def remove_stopwords(tokens):
    return [token for token in tokens if token not in stop_words]

def lemmatize_with_pos(tokens):
    pos_tags = pos_tag(tokens)
    lemmas = []
    for token, tag in pos_tags:
        wn_tag = get_wordnet_pos(tag)
        lemma = lemmatizer.lemmatize(token, pos=wn_tag) if wn_tag else lemmatizer.lemmatize(token)
        lemmas.append(lemma)
    return lemmas

def preprocess_text(text, use_spelling_correction=False, convert_numbers=False):
    text = text.lower()
    text = html.unescape(text)
    text = expand_contractions_and_acronyms(text)
    text = handle_web_elements(text)
    text = re.sub(r'[+-]?(\d*\.)?\d+', lambda m: num2words(m.group()), text)
    text = remove_punctuation(text)
    tokens = word_tokenize(text)
    tokens = remove_stopwords(tokens)
    tokens = lemmatize_with_pos(tokens)
    return ' '.join(tokens)

@pandas_udf(StringType())
def preprocess_text_udf(text_series):
    return text_series.apply(preprocess_text)

df_balanced = df_balanced.withColumn("Text_Preprocessed", preprocess_text_udf(df_balanced["Text"]))
df_balanced.show(5)
