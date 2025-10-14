# Project-Master
# 🎯 Aim
To automate Protest Event Analysis (PEA) using Natural Language Processing (NLP) and Large Language Models (LLMs) to analyse how UK media (The Guardian, The Times, The Telegraph) covered protests before, during, and after COVID-19.

# 🧩 Objectives
Develop an NLP pipeline (using LLMs) to detect and classify protest-related news.
Build a structured dataset of protest events (2020–2024).
Extract key features (date, place, actors, causes, methods).
Conduct sentiment and topic modelling, plus temporal and forecasting analysis of protest activity.

# 🧩 Work in Progress
1. Data Collection from MediaCloud
   - I began by downloading all relevant URLs from MIT MediaCloud.
   - The query targeted the UK–National and UK–State & Local collections, covering the period 2020–2024, and filtered for articles in English containing the words “protest” or “riot.”
   - (See screenshot: Captura de pantalla 2025-07-27 a las 15.54.35.png)
   - This query generated a dataset called URLS.csv.
     
2. Data Cleaning
   - Using the script FirstQuery.py, I cleaned the dataset to keep only the necessary columns and filter for the newspapers of interest: Daily Mail, The Telegraph, and The Guardian.
   - The Times was not included because it did not appear in the MediaCloud dataset.
     
3. Web Scraping Implementation
   - I created the Python file Scraple_article.py, which takes a single URL and extracts the full article text, saving it as a Word document.
   - Next, I developed fun_scraple.py, which defines the same scraping process as a reusable function.

4. Integration with MongoDB
   - The fun_scraple() function is called from conectar_mongo.py.
   - This script retrieves URLs from the MongoDB collection, runs the scraping function for each, and is designed to store the resulting articles directly in MongoDB for future processing.
   - Managed to get the URL from mongo, do the scrapping, and update the text to a new library in mongoDB.

5. 
   - I am going to make sure that my scrapping function works for the 3 papers that we are working with. 
   - The telegraph is not accessible (403 Client Error). Find a way to do the scrapping on the Telegraph (TO DO)

6. 
   - Make the code work for a large data set, since now it works for just one URL we want to use bucles, and threads to iterate the process (TO DO)
   - 