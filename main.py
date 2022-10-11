from __future__ import annotations
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import aiofiles
import os
import PyPDF2
  

from config import INFERENCE_DETECT_LANG, INFERENCE_SUMMARIZE, LANG_DICT
from utils import infer_sage_model, get_top_n_frequent_term, fetch_listings, retrive_json_file

app = FastAPI()

origins = [
    'http://localhost:3000',
    'sunyantra.netlify.app',
    'https://sunyantra.netlify.app',
    '*',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class ListingsRequestBody(BaseModel):
    request_params: str

@app.post("/fetch_listings")
def fetch_nasa_listings(body: ListingsRequestBody):
    """Fetches listings from NASA NTRS server but request body. 
    
    For example:
    ```javascript
        {
            "request_params":  "{ 'page': { 'size': 25, 'from': 0, }, 'highlight': True }"
        }
    ```

    """
    req_body = eval(body.request_params)
    return fetch_listings(req_body)

@app.get('/health')
def check_health():
    """
    Checks for the status of the server.
    """

    return {"status": "ok"}

@app.post("/analyze_file")
async def fetch_file_report(keyword_label: str = "computer science applications", in_file: UploadFile=File(...)):
    """
    Analyze the pdf_text from the input body and provide statistics like:
    - Summary of the text
    - Different type of language ratio used in the text
    - Top frequent words in the text
    - Simiar listings of documents related to keyword provided by the user

    Request Body:
    - **pdf_text**: Used to analyze the text
    - **keyword**: Used to get the similar listings
    \f
    :param item: User input.
    """
    async with aiofiles.open(in_file.filename, 'wb') as out_file:
        content = await in_file.read()  # async read
        await out_file.write(content)  # async write

    pdfFileObj = open(in_file.filename, 'rb')

    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    pageObj = pdfReader.getPage(0)

    # extracting text from page
    content = pageObj.extractText()[0:300]

    os.remove(in_file.filename)

    # lang_detect = eval(infer_sage_model(INFERENCE_DETECT_LANG, content))

    body = {
        'page': {
            'size': 10,
            'from': 0,
        },
        'highlight': True,
        'keyword': keyword_label
    }

    # for index in range(len(lang_detect)):
    #     lang_detect[index]["label"] = LANG_DICT[lang_detect[index]["label"]]

    response = {
        # "summarize_text": eval(infer_sage_model(INFERENCE_SUMMARIZE, content))[0]["summary_text"],
        "summarize_text": "NOT_AVAILABLE_NOW_DUE_TO_AWS_COST",
        # "language_detection": lang_detect,
        "language_detection": [{"label":"NOT_AVAILABLE_NOW_DUE_TO_AWS_COST","score":1}],
        "top_frequency_words": get_top_n_frequent_term(content),
        "similar_listings": fetch_listings(body)
    }
    return response


@app.get("/summarize")
def summarize(text: str):
    """Used to fetch the summary text of the input text"""
    summarize_text = eval(infer_sage_model(INFERENCE_SUMMARIZE, text))[0]["summary_text"]
    return summarize_text

@app.get("/detect_lang")
def detect_lang(text: str):
    """Used to fetch the ratio of language used in the text"""
    lang_detect = eval(infer_sage_model(INFERENCE_DETECT_LANG, text))

    for index in range(len(lang_detect)):
        lang_detect[index]["label"] = LANG_DICT[lang_detect[index]["label"]]

    return lang_detect

@app.get("/frequent_term")
def frequent_term(text: str):
    """Used to get the words with top frequency in the text"""
    return get_top_n_frequent_term(text)




@app.post("/upload")
async def post_endpoint(in_file: UploadFile=File(...)):
    # ...
    async with aiofiles.open(in_file.filename, 'wb') as out_file:
        content = await in_file.read()  # async read
        await out_file.write(content)  # async write

    pdfFileObj = open(in_file.filename, 'rb')

    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    pageObj = pdfReader.getPage(0)

    # extracting text from page
    extract_text = pageObj.extractText()
    os.remove(in_file.filename)


    return {"Result": extract_text}


@app.get("/fetch_analyzed_listings")
def fetch_analyzed_listings(offset: int = 0, limit: int = 25, keyword: str = "space and planetary science"):
    "Fetches custom analyzed text documents info"

    if offset > 1114:
        return {"error": "offset limit reached"}
    
    if limit > 100:
        limit = 25

    reponse = retrive_json_file('storage/analyze_documents.json', offset, limit)
    filter_with_keywords = [item for item in reponse if keyword in item["keywords"]]
    return filter_with_keywords