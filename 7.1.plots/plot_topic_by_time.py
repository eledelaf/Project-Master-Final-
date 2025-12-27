"""
plot_topic_by_time.py

This script plots the evolution of topics over time.
I want each topic to have a different color, create a plot that shows each topic vs time, so i can see when are we talking more about 
each one.
"""
import csv
import pandas as pd

import matplotlib.pyplot as plt

# 1. Load your CSV file
df = pd.read_csv('6.Topic analysis/topic_modeling/articles_with_topics.csv', sep=',', encoding='utf-8')

# 2. Select the desired columns
desired_columns = ['url','published_date', 'topic']
df_clean = df[desired_columns]

print(df_clean.head())

# 3. Plot each topic with a different color
plt.figure(figsize=(10, 6))
for topic in df_clean['topic'].unique():
    df_topic = df_clean[df_clean['topic'] == topic]
    plt.plot(df_topic['published_date'], df_topic['topic'], marker='o', linestyle='-', label=f'Topic {topic}')

plt.title('Topic vs. time')
plt.xlabel('Date')
plt.ylabel('Topic')
plt.legend()
plt.show()
