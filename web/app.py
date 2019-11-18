from flask import Flask, jsonify,make_response, request, render_template, redirect, url_for, session, logging
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
#api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def UserExist(username):
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True

def Verify_pw(username, password):

    hashed_pw = users.find({"Username" : username})[0]["Password"]
    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):

    tokens = users.find({"Username" : username})[0]["Tokens"]
    return tokens

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #GET form fields
        username = request.form["username"]
        password = request.form["password"]

        if UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "This user allready exist"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        retJson = {
            "status" : 200,
            "msg": "Successfully Signed up"
        }
        return jsonify(retJson)
    return render_template("signup.html")

@app.route("/detect", methods=["GET", "POST"])
def detect():
    if request.method == "POST":
        #GET form fields
        username = request.form["username"]
        password = request.form["password"]
        text1 = request.form["text1"]
        text2 = request.form["text2"]
        if not UserExist(username):
            retJson= {
                "status": 301,
                "msg" : "This user does not exist"
            }
            return jsonify(retJson)

        correct_pw = Verify_pw(username, password)

        if not correct_pw:
            retJson = {
                "status" : 302,
                "msg": "Sorry incorrect password"
            }
            return jsonify(retJson)

        num_tokens = countTokens(username)

        if num_tokens <= 0:
            retJson = {
                "status": 303,
                "msg": "Sorry you don't have enough tokens please buy more tokens"
            }
            return jsonify(retJson)

        # calculate the edit distance
        # load the Pre_trained model
        nlp = spacy.load("en_core_web_sm")

        text1 = nlp(text1)
        text2 = nlp(text2)

        # ratio is the number blw 0 and 1
        # the more similar text the more closer to one
        ratio = text1.similarity(text2)
        retJson= {
            "status": 200,
            "similiarity": ratio,
            "msg" : "Similarity Score Calculated successfully"
        }

        current_tokens = num_tokens - 1

        users.update({
            "Username": username
        },{
            "$set": {"Tokens" : current_tokens}
        })

        return jsonify(retJson)
    return render_template("model.html")

@app.route("/refill", methods=["GET", "POST"])
def refill():
    if request.method == "POST":
        #GET form fields
        username = request.form["username"]
        password = request.form["password"]
        refill_amount = request.form["refill"]

        if not UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "The admin is not registered"
            }
            return jsonify(retJson)

        correct_pw = "abc123"

        if not password == correct_pw:
            retJson = {
                "status": 302,
                "msg" : "password is not correct"
            }
            return jsonify(retJson)

        current_tokens = countTokens(username)

        users.update({
            "Username": username
        }, {
            "$set": {"Tokens" : current_tokens+1}
        })

        retJson = {
            "status": 200,
            "msg": "Refilled successfully"
        }
        return jsonify(retJson)
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug = True, host= "0.0.0.0")
