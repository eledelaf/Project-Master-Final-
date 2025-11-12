from fun_scraple import scrape_and_text
from fun_scraple import clean_middle_article


URL = 'https://www.standard.co.uk/lifestyle/sauna-etiquette-walhamstow-b1210234.html'
TITLE = 'A guide to sauna etiquette for Londoners... here\'s how not to embarras yourself'
TEXT = scrape_and_text(URL, TITLE)
text = clean_middle_article
print(text)

