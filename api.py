import bcrypt

from db import db, st, firebase
from flask import request
from flask_cors import CORS
from flask import Flask, jsonify

api = Flask(__name__)
CORS(api)

auth = firebase.auth()


# login applicant
@api.route('/loginApp', methods = ['POST'])
def login():
	param = request.get_json(force = True)
	userid = param.get('userid')
	passwd = param.get('passwd').encode('utf-8')

	applicants = db.child('applicants').child(userid).get().val()

	if applicants:
		if bcrypt.checkpw(passwd, applicants['hashpw']):
			return {'res': True, 'msg': 'Login Successful'}
		else:
			return {'res': False, 'msg': 'Wrong Password'}
	else:
		return {'res': False, 'msg': 'Username Not Registered'}

# signup applicant
@api.route('/signupApp', methods = ['POST'])
def signup():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd')
	
	user = auth.create_user_with_email_and_password(userid, passwd)
	if user:	
		return {'res': True, 'msg': 'Register Successful'}
	else:
		return {'res': False, 'msg': 'Register failed', 'err': user.error.errors}
	
# # update applicant
# @api.route('/updateApp', methods = ['POST'])
# def update():
# 	param = request.get_json(force = True)

