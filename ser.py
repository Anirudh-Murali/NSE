from multiprocessing import Process, Manager;
import requests
import sys
import twi2
import pickle
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from textblob.np_extractors import ConllExtractor
# from numba import vectorize
from flask import Flask
from flask_cors import CORS, cross_origin
from flask import jsonify
from flask import request

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import unicodedata
stop_words = stopwords.words('english')
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer

reload(sys)
sys.setdefaultencoding('utf-8')

porter = WordNetLemmatizer()

app = Flask(_name_)
CORS(app);

def getSentiment(arr,sharedResult,i,j,type):
    sid = SentimentIntensityAnalyzer();
    for m in range(i,j):
        #print(arr[m].encode("utf-8"));
        sentence = unicodedata.normalize('NFKD', arr[m])#.encode('ascii','ignore')
        ss = sid.polarity_scores(sentence)

        print("NEWS VALUES : ");
        print(ss['pos']);
        print(ss['neu']);
        print(ss['neg']);
        #print(arr[m].encode("utf-8"));

        if(abs(ss['pos'] - ss['neg']) < 0.065):
            sharedResult['neutral'] = sharedResult['neutral'] + 1;
        elif(ss['pos'] > ss['neg']):
            sharedResult['positive'] = sharedResult['positive'] + 1;
        else:
            sharedResult['negative'] = sharedResult['negative'] + 1;

        print("\nTYPE : " + str(type));
        print(sharedResult);

def getComplaints(topic, sharedComplaints):
    complaints = requests.get("http://webhose.io/filterWebContent?token=0a169495-89d3-4588-a475-32a7a91928b7&format=json&sort=crawled&q="+topic+"%20language%3Aenglish%20thread.country%3AIN%20site_type%3Adiscussions");
    cp = complaints.json()['posts'];
    count = 0;
    for text in cp:
        if text['thread']['site'] == "consumercomplaints.in":
            count = count + 1;
    sharedComplaints['total'] = count;
    print("## complaints fetched : " + str(count));

def getBlogs(topic, sharedDict):
    result = [];
    blogs = requests.get("http://webhose.io/filterWebContent?token=0a169495-89d3-4588-a475-32a7a91928b7&format=json&sort=crawled&q="+topic+"%20language%3Aenglish%20thread.country%3AIN%20site_type%3Ablogs")
    bl = (blogs.json()['posts'])[0:20];
    for text in bl:
        result.append(text['text']);
    sharedDict['blogs'] = result;
    print("### blogs fetched");

def getNews(topic, sharedDict):
    result = [];
    news = requests.get("http://webhose.io/filterWebContent?token=0a169495-89d3-4588-a475-32a7a91928b7&format=json&sort=crawled&q="+topic+"%20language%3Aenglish%20thread.country%3AIN%20site_type%3Anews")
    nw = (news.json()['posts'])[0:20];
    for text in nw:
        result.append(text['text']);
    sharedDict['news'] = result;
    print("### news fetched");


@app.route("/getDetails",methods=['POST'])
def everything():
    topic = request.form['topic'];
    topic1 = "";
    topic2 = "";
    if topic == "Punjab National Bank":
        topic1 = "pnb";
        topic2 = "@indiapnb";
    elif topic == "Infosys":
        topic1 = "infosys";
        topic2 = "@infosys";

    print(topic);
    print(topic1);
    print(topic2);

    manager = Manager();
    sharedDict = manager.dict();
    sharedNews = manager.dict({'positive':0, 'neutral':0, 'negative':0});
    sharedBlogs = manager.dict({'positive':0, 'neutral':0, 'negative':0});
    sharedTweet = manager.dict({'positive':0, 'neutral':0, 'negative':0})
    sharedComplaints = manager.dict({'total':0});

    blogs = Process(target=getBlogs, args=(topic1,sharedDict,));
    news = Process(target=getNews, args=(topic1,sharedDict,));
    tweets = Process(target=twi2.main, args=(topic2,sharedTweet,));
    complaints = Process(target=getComplaints, args=(topic1,sharedComplaints));

    blogs.start();
    news.start();
    tweets.start();
    complaints.start();
    blogs.join();
    news.join();
    tweets.join();
    complaints.join();

    #print(sharedDict);

    senti1 = Process(target=getSentiment, args=(sharedDict['news'],sharedNews,0,len(sharedDict['news'])/4,'news',));
    senti2 = Process(target=getSentiment, args=(sharedDict['news'],sharedNews,len(sharedDict['news'])/4,len(sharedDict['news'])/2,'news',));
    senti3 = Process(target=getSentiment, args=(sharedDict['news'],sharedNews,len(sharedDict['news'])/2,len(sharedDict['news'])*(3/4),'news',));
    senti4 = Process(target=getSentiment, args=(sharedDict['news'],sharedNews,len(sharedDict['news'])*(3/4),len(sharedDict['news']),'news',));

    senti5 = Process(target=getSentiment, args=(sharedDict['blogs'],sharedBlogs,0,len(sharedDict['blogs'])/4,'blogs'));
    senti6 = Process(target=getSentiment, args=(sharedDict['blogs'],sharedBlogs,len(sharedDict['blogs'])/4,len(sharedDict['blogs'])/2,'blogs',));
    senti7 = Process(target=getSentiment, args=(sharedDict['blogs'],sharedBlogs,len(sharedDict['blogs'])/2,len(sharedDict['blogs'])*(3/4),'blogs',));
    senti8 = Process(target=getSentiment, args=(sharedDict['blogs'],sharedBlogs,len(sharedDict['blogs'])*(3/4),len(sharedDict['blogs']),'blogs',));

    print("### sentiment analysis started");
    senti1.start();
    senti2.start();
    senti3.start();
    senti4.start();
    senti5.start();
    senti6.start();
    senti7.start();
    senti8.start();

    senti1.join();
    senti2.join();
    senti3.join();
    senti4.join();
    senti5.join();
    senti6.join();
    senti7.join();
    senti8.join();

    import json

    return jsonify(
        news = (dict(sharedNews)),
        blogs= (dict(sharedBlogs)),
        tweets=  (dict(sharedTweet)),
        complaints = dict(sharedComplaints)
    )

company = "";
result = 0;

@app.route("/sendNews",methods=['POST'])
def News():
    company2 = request.form['company'];
    news = request.form['news'];
    print(company2);
    company = company2;
    print(news);

    sid = SentimentIntensityAnalyzer()
    sentence = unicodedata.normalize('NFKD', news)
    ss = sid.polarity_scores(sentence)

    blob = TextBlob(news,analyzer=NaiveBayesAnalyzer())
    print (blob.sentiment)
    #
    # print(ss['pos']);
    # print(ss['neg']);
    # print(ss);

    if(ss['pos'] >= ss['neg']):
        global result
        result = 1;
    else:
        global result
        result = -1;

    print(result)
    return "aa gaya"

@app.route("/getUpdate",methods=['GET'])
def Update():
    global result
    result2 = result;
    result = 0;
    if result2 == 1:
        return "1";
    elif result2 == -1:
        return "-1";
    else:
        return "0";


if _name_ == '_main_':
    app.run(host='0.0.0.0');
