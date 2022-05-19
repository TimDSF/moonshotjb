import bcrypt

from db import db, st
from flask import request
from flask_cors import CORS
from flask import Flask, jsonify

# login applicant
@api.route('/loginApp', methods = ['POST'])
def login():
	param = request.get_json(force = True)
	userid = param.get('userid')
	passwd = param.get('passwd').encode('utf-8')

	applicants = db.child('applicants').child(userid).get().val()

	if applicants:
		if bcrypt.checkpw(password, applicants['hashpw']):
			return {'res': True, 'msg': 'Login Successful'}
		else:
			return {'res': False, 'msg': 'Wrong Password'}
	else:
		return {'res': False, 'msg': 'Username Not Registered'}

# signup applicant
@api.route('/loginApp', methods = ['POST'])
def signup():
	param = request.get_json(force = True)
	# todo

# update applicant
@api.route('/updateApp', methods = ['POST'])
def update():
	param = request.get_json(force = True)
