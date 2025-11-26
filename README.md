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
   - The telegraph is not accessible (403 Client Error). Find a way to do the scrapping on the Telegraph 
   - Is been 2 weeks and i havent found a way to do the scrapping on the telegraph so we are going to use another news paper with the same ideology thats on the MediaCloud Database 
   - Since I had to change the the telegraph to the standard, now we have a new daataset URLS_clean, with those 3 papers.
   - Lets check if the scrapping works in the standard, using Scraple_article.py, it works
6. 
   - Make the code work for a large data set, since now it works for just one URL we want to use bucles, and threads to iterate the process 
   - Instead of importing the URLS_clean to mongoDB I am going to create a new python file that takes the csv file from my computer and creates a new csv file with the article written on it (scrapple_to_csv.py)
   - In the scrape_to_csv file I took the information form URLS_clean and created the csv file with the columns i needed and added "time scrapped" and "text" that are empty at the moment.
   - Use the TEXTS.csv file and filled out
   - I created scrape_to_csv.py to do that, and saves it in scraped_data_checkpoints.csv and in scraped_data_final.csv
   - There is a problem because i was thinking on uploading the scraped_data_checkpoints.csv and the scraped_data_final.csv files in git hub but i cant so i have to use mongoDB

   - I managed to get the data in MongoDB but now, there is not enough space. There are two options here, do a bit of cleaning, bc when we do the scrapping the text is everything that is in the screen, and try to get the actuall text or pay to get more space. 
      - Clean the data before put it into mongoDB, like using the url as the id (Hecho)
      - or eliminating one of the time stamps
      - I am going to create a new function in fun_scraple in order to eliminate the headers and the footers.
      - Managed to do all the scrapping but using another scrapping function, trafilatura. Thats the new file fun_scrap_tra.py.
      - This function is not returning what i would hope for, so i need to find another way to clean a bit the data set.
      - Lets try newspaper3k, it seems like is working better.

   7. Classification model:
   7.1 sample set: 
   - First I am going to do a pre-filter with some more key words to have a group of possible articles that are more likely to be protest related. (DONE) classification.py. 
   - the first classification wasnt great, so i deacided to take out all of the articles that were under the sports, lifestyle, games... sections, so i rewrited classification.py.
   - We are only going to use the articles that have url = true.
   - We are going to use BERT or a LLM (Make it look for the context) for the classification,since i was looking to create a small data set and classify it myself then we would lose a lot of time. 
   - b: https://huggingface.co/docs/transformers/en/tasks/sequence_classification?utm_source=chatgpt.com
   - b: https://huggingface.co/docs/transformers/en/training?utm_source=chatgpt.com
   - b: https://huggingface.co/docs/transformers/en/model_doc/bert?utm_source=chatgpt.com
   - I am going to try A-Fine-tuned BERT, if this doesnt work i will try few-shot LLM (or if i have time to do both and compare)
   - We are going to do a sample set (sample_clasification.py) of 500 articles to train the BERT. The sample set will only take the as posible falses the ones that are url= true and keyword= false, and will take the posible true url = true and key word = true
   - I have downloaded the sample set (download_from_mongo.py)
   - I  have defined the articles that are positive: 
      - 1 = PROTEST if the article’s main focus is a collective, public action (demonstration, march, rally, strike, riot, blockade, occupation, picket, etc.) in which people express political or social claims. The article should describe the event itself (who, where, why, what happened), or its very immediate unfolding (clashes, arrests, dispersal, etc.).
      - 0 = NOT_PROTEST if the article is mainly about elite statements, scandals, normal politics, commentary, or other events where protests are only background or mentioned in passing.
   In sample_texts_with_labels.csv the column labels is the final classification 
   - Si hay tiempo deberia mejorar el sample set (sample_texts_with_candidate_refined.csv)

   7.2 Train fine-tune BERT:
   Bibliografia: Original BERT paper/Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019)./BERT:Pre-training of Deep Bidirectional Transformers for Language Understanding./Proceedings of NAACL-HLT.
   Bibliografia: DistilBERT paper / model/Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019)./DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter./Preprint: https://arxiv.org/abs/1910.01108
   bibliografia: https://arxiv.org/abs/1910.03771
   bibliografia: https://huggingface.co/docs/transformers/en/training?utm_source=chatgpt.com
   https://huggingface.co/docs/transformers/en/main_classes/tokenizer
   https://huggingface.co/docs/transformers/en/main_classes/trainer
   https://medium.com/@khang.pham.exxact/text-classification-with-bert-7afaacc5e49b

   We have a sample set of 500, of those 400 has been used to train it, 50 is for test and the other 50 are validation. 
   It returns:
      1. Accuracy ~ 0.82 → The model gets about 82% of all test articles right.
      2. Precision ~ 0.84 → Of everything the model calls “protest”, about 84% really are protest articles, and 16% are false alarms (non-protest articles misclassified as protest).
      3. Recall ~ 0.87 → Of all the true protest articles in the test set, the model correctly finds about 87%, and misses about 13% (false negatives).
      4. F1 ~ 0.86 → Overall balance between precision and recall is strong; it’s a solid classifier for a small dataset.
   - TO DO: Do a quick error analysis looking at a few false positives and false negatives.
   - TO DO: no lo puedo subir a git pq bert_protest_binary/checkpoint-150/optimizer.pt is 510.91 MB; this exceeds GitHub's file size limit of 100.00 MB 

   7.4 Do the classification:

   7.5 validar la calisificación?


