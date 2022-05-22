import os
import time
import bcrypt
import random
import string

from db import db, st, firebase
from flask import request
from flask_cors import CORS
from flask import Flask, jsonify

UPLOAD_FOLDER = './uploads'
MAX_SIZE = 10240 # in bytes
ALLOWED_FORMATS = {'pdf'}

api = Flask(__name__)
api.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api.config['MAX_CONTENT_PATH'] = MAX_SIZE
# CORS(api)

# login applicant
@api.route('/loginApp', methods = ['POST'])
def loginApp():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd').encode('utf-8')

	applicants = db.child('applicants').child(userid).get().val()

	if applicants:
		if bcrypt.checkpw(passwd, applicants['hashpw'].encode('utf-8')):
			token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 256))
			data = {
				'login': {
					'token': token,
					'expiration': time.time() + 86400
				}
			}
			db.child('applicants').child(userid).set(data)
			return {'res': 0, 'msg': 'Successful'}
		else:
			return {'res': 2, 'msg': 'Wrong Password'}
	else:
		return {'res': 1, 'msg': 'Username Not Registered'}

# signup applicant
@api.route('/signupApp', methods = ['POST'])
def signupApp():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd').encode('utf-8')
	
	if db.child('applicants').child(userid).get().val():
		return {'res': 1, 'msg': 'User ID Occupied'}
	else:
		hashpw = bcrypt.hashpw(passwd, bcrypt.gensalt()).decode('utf-8')
		token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 256))
		print(hashpw, token)
		data = {
				'hashpw': hashpw,
				'guest': False,
				'login': {
					'token': token,
					'expiration': time.time() + 86400
				}
			}
		db.child('applicants').child(userid).set(data)
		return {'res': 0, 'msg': 'Successful', 'token': token}
	
# update applicant
# note: in order to have the file uploaded successfully, the html form needs to have encryption of enctype="multipart/form-data"
@api.route('/updateApp', methods = ['POST'])
def updateApp():
	data = request.form.to_dict()

	data.pop('tag[]', None)
	data['tags'] = request.form.getlist('tag[]')

	data['workAuth'] = True if data['workAuth'] == 'true' else False
	data['contacts'] = {
		'number': data.pop('number', None),
		'wxid': data.pop('wxid', None),
		'email': data.pop('email', None)
	}
	data['education'] = {
		'college': data.pop('college', None),
		'degree': data.pop('degree', None)
	}
	data['experience'] = {
		'yearsExp': data.pop('yearsExp', None),
		'numsEmp': data.pop('numsEmp', None)
	}
	data['externalLinks'] = {
		'LinkedIn': data.pop('LinkedIn', None),
		'Github': data.pop('GitHub', None),
		'GoogleScholar': data.pop('GoogleScholar', None),
		'personalWebsite': data.pop('personalWebsite', None)
	}
	
	userid = data['userid']
	token = data.pop('token')

	if 'resume' in request.files:
		file = request.files['resume']
		extension = file.filename.split('.')[-1]
		filename = 'resume_'+userid+'.'+extension

		if not file or file.filename == '':
			return {'res': 4, 'msg': 'No Resume Uploaded'}
		elif extension not in ALLOWED_FORMATS:
			return {'res': 5, 'msg': 'Unsupported Resume Format'}
		else:
			file.save(os.path.join(UPLOAD_FOLDER, filename))

	# data['resume'] = 'resumes/' + filename
	# st.child(data['resume']).put(os.path.join(UPLOAD_FOLDER, filename))

	if db.child('applicants').child(userid).get().val():
		if token != db.child('applicants').child(userid).child('login').child('token').get().val():
			return {'res': 2, 'msg': 'Mismatch Token'}
		elif time.time() > db.child('applicants').child(userid).child('login').child('expiration').get().val():
			return {'res': 3, 'msg': 'Session Expired'}
		else:
			db.child('applicants').child(userid).update(data)
			return {'res': 0, 'msg': 'Successful'}
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

