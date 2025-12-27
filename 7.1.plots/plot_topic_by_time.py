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
df = pd.read_csv('6.Topic_analysis/topic_modeling/articles_with_topics.csv', sep=',', encoding='utf-8')

# 2. Select the desired columns
desired_columns = ['url','published_date', 'topic']
df_clean = df[desired_columns]
print(df_clean.head())

df_clean['published_date'] = pd.to_datetime(df_clean['published_date'])

# drop rows where published_date is null
df_clean = df_clean.dropna(subset=['published_date'])

# Choose the topics and give them names 
topic = {
    -1: "BLM UK",
    0: "Capitol",
    1: "Anti-immigration UK",
    2: "BLM USA",
    4: "COVID UK",
    5: "Gaza",
    6: "COVID EU",
    7: "Ukraine"
}

# Filter by topic 
df_clean = df_clean[df_clean['topic'].isin(topic.keys())]


# 3. Make month-year bins
df_clean['month_year'] = df_clean['published_date'].dt.to_period('M').dt.to_timestamp()

# 3.1 Count articles per topic and month
topic_month_counts = df_clean.groupby(['month_year', 'topic']).size().reset_index(name='count')

# 4. Plot the evolution of topics over time
plt.figure(figsize=(12, 6))
for topic_id, topic_name in topic.items():
    data = topic_month_counts[topic_month_counts['topic'] == topic_id]
    plt.plot(data['month_year'], data['count'], label=topic_name)

plt.xlabel('Month-Year')
plt.ylabel('Number of Articles')
plt.title('Evolution of Topics Over Time')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()