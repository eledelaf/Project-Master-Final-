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
   - ERROR GITHUB:
   > git push origin main:main
      remote: error: Trace: 3dd4b00f48f997f2277a24d2d0a4729d959a19ec21485dd11ff8dceae4fb8572        
      remote: error: See https://gh.io/lfs for more information.        
      remote: error: File bert_protest_binary/checkpoint-150/model.safetensors is 255.43 MB; this exceeds GitHub's file size limit of 100.00 MB        
      remote: error: File bert_protest_binary/checkpoint-150/optimizer.pt is 510.91 MB; this exceeds GitHub's file size limit of 100.00 MB        
      remote: error: GH001: Large files detected. You may want to try Git Large File Storage - https://git-lfs.github.com.        
      To github.com:eledelaf/Project-Master.git
      ! [remote rejected] main -> main (pre-receive hook declined)
      error: failed to push some refs to 'github.com:eledelaf/Project-Master.git'
      He hecho esto:
      (.venv) (base) elenadelafuente@MacBook-Air-de-Elena Project-Master % git rm --cached bert_protest_binary/checkpoint-150/model.safetensors
      rm 'bert_protest_binary/checkpoint-150/model.safetensors'
      (.venv) (base) elenadelafuente@MacBook-Air-de-Elena Project-Master % git rm --cached bert_protest_binary/checkpoint-150/optimizer.pt
      rm 'bert_protest_binary/checkpoint-150/optimizer.pt'
      (.venv) (base) elenadelafuente@MacBook-Air-de-Elena Project-Master % git commit --amend -CHEAD
      [main 61d90f8] ns
      Date: Thu Nov 27 16:02:42 2025 +0000
      3 files changed, 0 insertions(+), 0 deletions(-)
      delete mode 100644 bert_protest_binary/checkpoint-150/model.safetensors
      delete mode 100644 bert_protest_binary/checkpoint-150/optimizer.pt
      (.venv) (base) elenadelafuente@MacBook-Air-de-Elena Project-Master % git push
      No se si las cosas que he eliminado son importantes
      me ha vuelto a dar este error:
      > git push origin main:main
      remote: error: Trace: aa2f1fee306ba2217bffbfa0d2a12cf9feaf162a722b3c3c662649ce0efc409f        
      remote: error: See https://gh.io/lfs for more information.        
      remote: error: File bert_protest_binary/checkpoint-150/model.safetensors is 255.43 MB; this exceeds GitHub's file size limit of 100.00 MB        
      remote: error: File bert_protest_binary/checkpoint-150/optimizer.pt is 510.91 MB; this exceeds GitHub's file size limit of 100.00 MB        
      remote: error: GH001: Large files detected. You may want to try Git Large File Storage - https://git-lfs.github.com.        
      To github.com:eledelaf/Project-Master.git
       ! [remote rejected] main -> main (pre-receive hook declined)
      error: failed to push some refs to 'github.com:eledelaf/Project-Master.git'
      - If BERT does not work out: https://www.kaggle.com/code/mehmetlaudatekman/text-classification-svm-explained
      - Error analysis
      This are the False positives and False negative:
      Number of false positives: 5
      Number of false negatives: 5

      --- Sample false positives (model thought they were protests, but labels say no) ---

      URL: https://www.dailymail.co.uk/news/article-11449565/Morgan-Freeman-dominates-World-Cup-opening-ceremony-2022.html?ns_mchannel=rss&ito=1490&ns_campaign=1490
      TITLE: Qatar World Cup: Rows of empty seats as 'fans' leave early and Morgan Freeman hosts opening ceremony
      TRUE LABEL: 0 PRED: 1

      URL: https://www.dailymail.co.uk/news/article-10619389/Kyrsten-Sinema-told-Biden-NOT-come-Arizona-signed-COVID-rescue-plan.html
      TITLE: Kyrsten Sinema told Biden NOT to come to Arizona after he signed the COVID rescue plan
      TRUE LABEL: 0 PRED: 1

      URL: https://www.dailymail.co.uk/news/article-9990639/Justice-Stephen-Breyer-calls-SCOTUS-decision-allow-Texas-abortion-ban-bad.html?ns_mchannel=rss&ns_campaign=1490&ito=1490
      TITLE: Justice Stephen Breyer calls SCOTUS decision to allow Texas abortion ban 'very bad'
      TRUE LABEL: 0 PRED: 1

      URL: https://www.theguardian.com/world/2023/feb/08/turkey-and-syria-earthquake-what-we-know-so-far-on-day-three
      TITLE: Turkey and Syria earthquake: what we know so far on day three
      TRUE LABEL: 0 PRED: 1

      URL: https://www.dailymail.co.uk/news/article-8614877/Shocking-moment-partygoers-throw-objects-police-illegal-cookout-rave-Kent-beach.html?ns_mchannel=rss&ito=1490&ns_campaign=1490
      TITLE: Shocking moment partygoers throw objects at police at illegal 'cookout' rave on Kent beach
      TRUE LABEL: 0 PRED: 1

      From the False postive we can see the following:
      1. False positives (model says protest = 1, label says 0)
      1) Qatar World Cup opening ceremony
      Rows of empty seats as 'fans' leave early… opening ceremony
      Big crowd, stadium, “rows of empty seats” → looks like an event, but not a protest.
      Model probably got triggered by: crowd / stadium context, maybe words like “fans”, “leave”, “boos”, etc. in the text.
      Conclusion: genuine false positive. Not a protest by your definition.
      2) Kyrsten Sinema / Biden in Arizona
      Told Biden NOT to come… after he signed the COVID rescue plan
      This is elite politics / strategy, not people in the streets.
      No collective public claim-making event.
      Conclusion: model overfits on terms like Biden, COVID, Arizona and maybe “rally” or “visit” in the text → another real FP.
      3) Justice Breyer on Texas abortion ban
      SCOTUS decision to allow Texas abortion ban 'very bad'
      Again, this is judicial / elite commentary, not an on-the-ground protest.
      There might be protest mentions (people protesting the law), but they’re background, not the main focus.
      Conclusion: good that your label is 0. Model is probably keying too hard on “abortion ban” + maybe “protests” somewhere in text→FP.
      4) Turkey and Syria earthquake – day three
      Earthquake: what we know so far on day three
      Disaster coverage. There might be mentions of anger/fury, but the core is natural disaster, not protest event.
      Model might be confused if text has “crowds gather”, “anger grows”, “looting” etc. → looks protest-ish lexically.
      Conclusion: another false positive. This shows the model sometimes confuses riot/chaos/disaster with protest.
      5) Partygoers throwing objects at police at illegal rave
      …throw objects at police at illegal 'cookout' rave on Kent beach
      This one is interesting.
      Is this a protest? Probably no by your strict definition:
      It’s an illegal party / rave, not a political or social claim.
      Yes, there’s collective action and confrontation with police, but no clear grievance or demand.
      The model sees: “throw objects at police”/“illegal”/“partygoers” / crowd → looks a lot like a riot event, so it says “1”.
      Conclusion: From a political violence perspective this is “contentious crowd event”, but for PEA-protest you decided to require claim-making, so it’s a false positive.
      Pattern in FPs
      Your false positives are: crowd + police + conflict (rave, possibly earthquake chaos), or highly politicised topics without an actual street event (SCOTUS, Sinema, etc.). So the model has learned “protest-like situations”, but not always your stricter “protest event” boundary. That’s normal and actually not a disaster – your definition is narrower than “any public conflict”.

      --- Sample false negatives (real protests that the model missed) ---

      URL: https://www.dailymail.co.uk/news/article-11341215/How-multimillionaire-Steve-Bannon-went-White-House-jail-sentence.html?ns_mchannel=rss&ns_campaign=1490&ito=1490
      TITLE: How the multimillionaire Steve Bannon went from the White House to jail sentence
      TRUE LABEL: 1 PRED: 0

      URL: https://www.theguardian.com/world/2020/aug/17/la-caravana-del-diablo-a-migrant-caravan-in-mexico-photo-essay
      TITLE: La Caravana del Diablo: a migrant caravan in Mexico – photo essay
      TRUE LABEL: 1 PRED: 0

      URL: https://www.dailymail.co.uk/news/article-8509647/Goat-trim-Mountain-goats-form-orderly-queue-outside-barbers-Welsh-town.html?ns_mchannel=rss&ito=1490&ns_campaign=1490
      TITLE: Goat to get a trim! Mountain goats form orderly queue outside barbers in Welsh town
      TRUE LABEL: 1 PRED: 0

      URL: https://www.theguardian.com/environment/2021/jul/03/mount-rushmore-south-dakota-indigenous-americans
      TITLE: The battle for Mount Rushmore: ‘It should be turned into something like the Holocaust Museum’
      TRUE LABEL: 1 PRED: 0
      In your error list it was:
      TRUE LABEL: 1, PRED: 0
      I would keep it as 1 and maybe even mark it in your notes as:
      “Protest article with broader contextual/historical content.”
      This is a good example for your thesis of:
      The kind of nuanced protest coverage you care about, and
      A type of article that BERT can sometimes miss (false negative), because the word “protest” / “march” may appear relatively few times, surrounded by a lot of historical and political explanation.
      You can even mention it explicitly in your “Error analysis” section as a case where:
      The model struggled with an article that blends event description + structural context, even though it clearly fits your protest-event definition.
      If you want, we can go through the migrant caravan article next and decide if you want that one labelled 1 or 0, so your codebook stays consistent.

      URL: https://www.standard.co.uk/news/politics/arrests-police-protests-london-palestine-israel-arms-b1154930.html
      TITLE: Three arrests as police deal with 'number of protests' in Westminster
      TRUE LABEL: 1 PRED: 0
      In this case is not classifying it well becasue the scrapping failed and we only have a small fracment of the article.

      Some of the False negatives are errors on the labeling, so i have to change that (cambiar_csv.py). Also the other error that we are getting is that the model does not asumes a pacific protest as a protest since we are focusing on riots and violence.

      Test metrics after doing some changes on the data set: 
      Test metrics: {'eval_loss': 0.32307156920433044, 'eval_accuracy': 0.8, 'eval_precision': 0.8, 'eval_recall': 0.8571428571428571, 'eval_f1': 0.8275862068965517, 'eval_runtime': 1.4704, 'eval_samples_per_second': 34.004, 'eval_steps_per_second': 2.72, 'epoch': 3.0}
      Test metrics: {'eval_loss': 0.2740192115306854, 'eval_accuracy': 0.88, 'eval_precision': 0.84375, 'eval_recall': 0.9642857142857143, 'eval_f1': 0.9, 'eval_runtime': 1.6952, 'eval_samples_per_second': 29.496, 'eval_steps_per_second': 2.36, 'epoch': 3.0}
      
   7.4 Do the classification:
   I have to get the info from MONGODB and do the classification, and update the mongo db database to get the classification done (bert_classification.py)
   I am only going to classify the url_candidate = True

   7.5 validar la calisificación?
   The first step are the test metric from the trainig model file 
   We are going to separate the data base depending on the bert_score.
   * High-confidence protest: bert_protest_label = 1 and bert_protest_score ≥ 0.8
   * Borderline protest: bert_protest_label = 1 and 0.5 ≤ score < 0.8
   * High-confidence non-protest: bert_protest_label = 0 and score ≥ 0.8  
   * Borderline non-protest: bert_protest_label = 0 and 0.5 ≤ score < 0.8
   After that we are goin gto get a sample of 30 articles of each section and check manually. We will add a human label on each of them and then compare them to the BERT model label.



