import bcrypt

from db import db, st
from flask import request
from flask_cors import CORS
from flask import Flask, jsonify

print(db.child('applicants').child('timdsf').get().val()['hashpw'])
