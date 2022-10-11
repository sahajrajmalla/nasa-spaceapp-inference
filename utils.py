import boto3
import json
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, STOP_WORDS
from collections import Counter
import requests
import re
import string

def infer_sage_model(INFERENCE_URL, content):
    json_input = {
    "inputs": [content]
    }

    client = boto3.client('sagemaker-runtime',
        region_name="us-east-2",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    response = client.invoke_endpoint(
        EndpointName=INFERENCE_URL,
        Body=json.dumps(json_input),
        ContentType= "application/json",
    )
    result = response['Body'].read().decode()
    return result

def clean_text(text):
    text = ''.join([word.lower() for word in text if word not in string.punctuation])
    tokens = re.split('\W+', text)
    text = [word for word in tokens if word not in STOP_WORDS and len(word) >= 4]
    return text

def get_top_n_frequent_term(data_set):
    
    split_it = clean_text(data_set)   
    counter = Counter(split_it)
    most_occur = counter.most_common(10)
    
    return most_occur


def fetch_listings(body):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://ntrs.nasa.gov/search',
        'Origin': 'https://ntrs.nasa.gov',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    response = requests.post('https://ntrs.nasa.gov/api/citations/search', headers=headers, json=body)
    return response.json()["results"] 


def retrive_json_file(file_path, offset, limit):
    with open(file_path, 'r+') as openfile:
        json_object = json.load(openfile)

    return json_object[offset : offset + limit]
