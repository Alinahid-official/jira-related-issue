from pymongo import MongoClient
import json
import pymongo
from nltk.stem import PorterStemmer
import string
import re
# from dotenv import load_dotenv
import os




from flask import Flask, render_template, request, url_for, Response
from bs4 import BeautifulSoup
import numpy as np
from flask import jsonify
from sympy import inv_quick

from flask_cors import CORS

# MONGODB_URI =  "mongodb+srv://jira:Deepika@cluster0.g4ll0.mongodb.net/?retryWrites=true&w=majority"
MONGODB_URI="mongodb+srv://demo:demo123@jira.zrnz9.mongodb.net/?retryWrites=true&w=majority"
# initiate flask
app = Flask(__name__)
CORS(app)
# Mongodb database connection


cluster = MongoClient(
    MONGODB_URI
   )

print(cluster["test"])
print("@@@@@@@@@@@@@@@@@@@@@")
print("")
db = cluster["test"]

print(db["inverted"])
print("@@@@@@@@@@@@@@@@@@@@@")
print("")
collection = db["inverted"]


def decontracted(phrase):
    # specific
    phrase = re.sub(r"won't", "will not", phrase)
    phrase = re.sub(r"can\'t", "can not", phrase)

    # general
    phrase = re.sub(r"n\'t", " not", phrase)
    phrase = re.sub(r"\'re", " are", phrase)
    phrase = re.sub(r"\'s", " is", phrase)
    phrase = re.sub(r"\'d", " would", phrase)
    phrase = re.sub(r"\'ll", " will", phrase)
    phrase = re.sub(r"\'t", " not", phrase)
    phrase = re.sub(r"\'ve", " have", phrase)
    phrase = re.sub(r"\'m", " am", phrase)
    return phrase


ps = PorterStemmer()
stopwords = set(['br', 'the', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
                "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
                 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their',
                 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those',
                 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
                 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
                 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
                 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                 'most', 'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're',
                 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn',
                 "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',
                 "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't",
                 'won', "won't", 'wouldn', "wouldn't", ""])


@app.route('/index', methods=['POST'])
def index():
    if request.method == 'POST':

        data = request.get_json()
        print(data["document"])  # one collection
        print(db.issues.count_documents({}))

        try:

            if (db.inverted_index.count_documents({}) == 0):

                db.inverted_index.insert_one({})

            idd = [data["issue_id"], data["project_id"]]

        except Exception as ex:
            print(ex)
            return jsonify({"message": "failed"})

        print(db.inverted)
        inv_index = db["inverted_index"].find({})[0]

        print(inv_index)
        # print(list(inv_index)[0])
        # return "str"
        # tags = db.tag.find()[0]

        # idd = 123 #(ur task)
        text = data["document"]

        sentance = re.sub(r"http\S+", "", text)
        sentance = BeautifulSoup(sentance, 'html').get_text()
        sentance = decontracted(sentance)
        sentance = re.sub("\S*\d\S*", "", sentance).strip()

        tokens = sentance.split()
        tokens = [token.lower() for token in tokens]
        l = []
        for x in tokens:

            l.append(re.sub(r'[^a-z]', '', x))

        sentance = " ".join(l)
        tokens = sentance.split()

        tokens = [token for token in tokens if token not in stopwords]
        tokens = [ps.stem(token) for token in tokens]
        Id = str(idd)

        for x in set(tokens):

            if x in inv_index.keys():
                inv_index[x]["IDs"].append(
                    {Id: tokens.count(x), "TF": (tokens.count(x)/len(tokens))})
                inv_index[x]["idf"] = tokens.count(x) + inv_index[x]["idf"]
            else:

                inv_index[x] = {}
                inv_index[x]["IDs"] = []

                inv_index[x]["IDs"].append(
                    {Id: tokens.count(x), "TF": (tokens.count(x)/len(tokens))})
                inv_index[x]["idf"] = tokens.count(x)

        # for x in set(d["tags"]):

        #     if x in tags.keys():
        #         tags[x].append(Id)
        #     else:

        #         tags[x] = []
        #         tags[x].append(Id)

        # print(inv_index)
        # print(tags)

        try:
            db.inverted_index.drop()
            dbResponse = db.inverted_index.insert_one(inv_index)

        except Exception as ex:
            print(ex)

            return jsonify({"message": "failed"})

    return jsonify({"message": "success"})


@app.route('/search', methods=['GET'])
def search():
    if request.method == 'GET':
        # print('yes')
        n = db.datas.count_documents({})
        query = request.args.get("search")
        print(query)
        tokens = query.split()
        tokens = [token.lower() for token in tokens]
        print(tokens)
        l = []
        for x in tokens:

            l.append(re.sub(r'[^a-z]', '', x))

        sentance = " ".join(l)
        tokens = sentance.split()

        tokens = [token for token in tokens if token not in stopwords]
        tokens = [ps.stem(token) for token in tokens]

        inv_index = db.inverted_index.find({})[0]
        # tags = db.tag.find()[0]

        print(tokens)
        S = {}
        for x in set(tokens):
            if x in inv_index.keys():
                print(x)
                print(inv_index[x])
                for y in inv_index[x]["IDs"]:
                    print(y)

                    try:
                        S[list(y.keys())[0]] = S[list(y.keys())[0]] + \
                            (y["TF"] * np.log((n/inv_index[x]["idf"])))

                    except:

                        S[list(y.keys())[0]] = y["TF"] * \
                            np.log((n/inv_index[x]["idf"]))

        print(S)
        s = sorted(S.items(), key=lambda x: x[1], reverse=True)
        k = [x[0] for x in s]
        if len(k) <= 5:
            pass
        else:
            k = k[0:5]

        print(k)
# Related
        return jsonify({"Issues": k})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
