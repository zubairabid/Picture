from app import app, db, photos
from app.models import User, Post
import re

def tagger(text):
    print("Some text has been sent for tagging!")
    mentionList = re.findall(r'@\w*', text)
    for mention in mentionList:
        print("Looking at mention " + mention)
        if User.query.filter_by(username=mention[1:]).first() is not None:
            newmention = '<a href="http://localhost:5000/user/'+ mention[1:] +'">@' + mention[1:] + '</a>'
            text = re.sub(mention, newmention, text)
            print("tried to make a replacement, as user with mention was found")

    return text
