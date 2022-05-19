import pyrebase
from flask import Flask

app = Flask(__name__)

firebaseConfig = {
  'apiKey': "AIzaSyAr0ZiK8MNaCaV1TNf4bKXiPYx1s_6v5e0",
  'authDomain': "moonshot-b9978.firebaseapp.com",
  'projectId': "moonshot-b9978",
  'databaseURL': "https://moonshot-b9978-default-rtdb.firebaseio.com",
  'storageBucket': "moonshot-b9978.appspot.com",
  'messagingSenderId': "1021812571433",
  'appId': "1:1021812571433:web:b79d02f04e352e56744b38",
  'measurementId': "G-E0ZSHXXNNF"
};

firebase = pyrebase.initialize_app(firebaseConfig)

db = firebase.database()