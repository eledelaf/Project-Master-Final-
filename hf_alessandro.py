# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-generation", model="network-centrality-labs/uk-news2")
messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe(messages)