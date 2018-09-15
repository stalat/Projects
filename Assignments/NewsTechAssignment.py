# python standard functions
import re
import json

# TP packages installed for specific purpose
import boto3
import requests
import html2text
from bs4 import BeautifulSoup

# URL that needs to get processed
url = "https://blogs.wsj.com/cio/2018/06/18/software-microservices-open-up-new-business-models-for-companies/"
html_content = requests.get(url)

# Utility to get tex content from HTML blog
converter = html2text.HTML2Text()

# CleanUp process is been done in further steps
text = converter.handle(html_content.text)
content_without_urls = re.sub(r'http\S+', '', text)
desc_confidence_score = {}
comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')


def get_score(text_content):
    """
    Here, I have iterated over the content splitted by '.' as comprehend API wasn't able to
    process the huge data at once due to it's limit for 5000 bytes. May need to explore to improve
    the performance
    """
    for item in text_content.split('.'):
        if len(item) == 0:
            continue

        # Here, I have used comprehend API provided by AWS
        interm_result = comprehend.detect_key_phrases(Text=item, LanguageCode='en')
        for val in interm_result.get('KeyPhrases'):
            # setting up the key-phrased along with it's score
            desc_confidence_score[val.get('Text')] =  val.get('Score')

        # Showing up the final result with descending score for key-phrases
    return sorted(desc_confidence_score.items(), key=lambda x: x[1], reverse=True)


content_without_sp_char = re.sub("[^A-Za-z0-9.\']+", " ", content_without_urls)
resultant = get_score(content_without_sp_char)
for res in resultant:
    print(res)
