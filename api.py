import os
import time
import bcrypt
import random
import string

from db import db, st, firebase
from flask_cors import CORS
from flask import Flask, request, jsonify
from datetime import date

UPLOAD_FOLDER = './uploads'
MAX_SIZE = 10240 # in bytes
ALLOWED_FORMATS = {'pdf'}

api = Flask(__name__)
api.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api.config['MAX_CONTENT_PATH'] = MAX_SIZE
# CORS(api)

# test
@api.route('/test', methods = ['GET'])
def test():
    return 'successful'

# login applicant
@api.route('/loginApp', methods = ['POST'])
def loginApp():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd').encode('utf-8')

	applicants = db.child('applicants').child(userid).get().val()

	if applicants:
		if bcrypt.checkpw(passwd, applicants['hashpw'].encode('utf-8')):
			token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 32))
			data = {
				'login': {
					'token': token,
					'expiration': time.time() + 86400
				}
			}
			db.child('applicants').child(userid).update(data)
			return {'res': 0, 'msg': 'Successful', 'token': token}
		else:
			return {'res': 2, 'msg': 'Wrong Password'}
	else:
		return {'res': 1, 'msg': 'Username Not Registrated'}

# signup applicant
@api.route('/signupApp', methods = ['POST'])
def signupApp():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd').encode('utf-8')
	
	if db.child('applicants').child(userid).get().val():
		return {'res': 1, 'msg': 'User ID Occupied'}
	else:
		hashpw = bcrypt.hashpw(passwd, bcrypt.gensalt()).decode('utf-8')
		token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 32))
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

# signup guest
@api.route('/signupGuest', methods = ['POST'])
def signupGuest():
	userid = request.form.get('userid')
	
	if db.child('applicants').child(userid).get().val():
		return {'res': 1, 'msg': 'User ID Occupied'}
	else:
		
		data = {
				'guest': True
			}
		db.child('applicants').child(userid).set(data)
		return {'res': 0, 'msg': 'Successful'}
	
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
		'yearsExp': int(data.pop('yearsExp', None)),
		'numsEmp': int(data.pop('numsEmp', None))
	}
	data['externalLinks'] = {
		'LinkedIn': data.pop('LinkedIn', None),
		'Github': data.pop('GitHub', None),
		'GoogleScholar': data.pop('GoogleScholar', None),
		'personalWebsite': data.pop('personalWebsite', None)
	}
	data['applications'] = []
	
	userid = data.pop('userid')
	token = data.pop('token')

	# st.child(data['resume']).put(os.path.join(UPLOAD_FOLDER, filename))

	if db.child('applicants').child(userid).get().val():
		if token != db.child('applicants').child(userid).child('login').child('token').get().val():
			return {'res': 2, 'msg': 'Mismatch Token'}
		elif time.time() > db.child('applicants').child(userid).child('login').child('expiration').get().val():
			return {'res': 3, 'msg': 'Session Expired'}
		else:
			if 'resume' in request.files:
				file = request.files['resume']
				extension = file.filename.split('.')[-1]
				filename = 'resume_'+userid+'.'+extension

				if not file or file.filename == '':
					return {'res': 4, 'msg': 'No Resume Uploaded'}
				elif extension not in ALLOWED_FORMATS:
					return {'res': 5, 'msg': 'Unsupported Resume Format'}
				else:
					data['resume'] = True
					file.save(os.path.join(UPLOAD_FOLDER, filename))
			
			db.child('applicants').child(userid).update(data)
		
			return {'res': 0, 'msg': 'Successful'}
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

# login recruiter
@api.route('/loginRec', methods = ['POST'])
def loginRec():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd').encode('utf-8')

	recruiters = db.child('recruiters').child(userid).get().val()

	if recruiters:
		if bcrypt.checkpw(passwd, recruiters['hashpw'].encode('utf-8')):
			token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 32))
			data = {
				'login': {
					'token': token,
					'expiration': time.time() + 86400
				}
			}
			db.child('recruiters').child(userid).update(data)
			return {'res': 0, 'msg': 'Successful', 'token': token}
		else:
			return {'res': 2, 'msg': 'Wrong Password'}
	else:
		return {'res': 1, 'msg': 'Username Not Registrated'}

# signup recruiter
@api.route('/signupRec', methods = ['POST'])
def signupRec():
	userid = request.form.get('userid')
	passwd = request.form.get('passwd').encode('utf-8')
	
	if db.child('recruiters').child(userid).get().val():
		return {'res': 1, 'msg': 'User ID Occupied'}
	else:
		hashpw = bcrypt.hashpw(passwd, bcrypt.gensalt()).decode('utf-8')
		token = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 32))
		print(hashpw, token)
		data = {
				'hashpw': hashpw,
				'login': {
					'token': token,
					'expiration': time.time() + 86400
				}
		}
		db.child('recruiters').child(userid).set(data)
		return {'res': 0, 'msg': 'Successful', 'token': token}

# update recruiter
# note: in order to have the file uploaded successfully, the html form needs to have encryption of enctype="multipart/form-data"
@api.route('/updateRec', methods = ['POST'])
def updateRec():
	data = request.form.to_dict()

	data['contacts'] = {
		'name': data.pop('name', None),
		'phone': data.pop('phone', None),
		'email': data.pop('email', None)
	}
	
	data['companyDescription'] = {
		'description': data.pop('description', None),
		'background': data.pop('background', None),
		'financing': data.pop('financing', None),
	}
	data['verified'] = False
	userid = data.pop('userid')
	token = data.pop('token')

	if db.child('recruiters').child(userid).get().val():
		if token != db.child('recruiters').child(userid).child('login').child('token').get().val():
			return {'res': 2, 'msg': 'Mismatch Token'}
		elif time.time() > db.child('recruiters').child(userid).child('login').child('expiration').get().val():
			return {'res': 3, 'msg': 'Session Expired'}
		else:
			db.child('recruiters').child(userid).update(data)

			return {'res': 0, 'msg': 'Successful', 'data': data}
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

# readApp 
@api.route('/readApp', methods = ['POST'])
def readApp():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	targetid = data.pop('targetid')

	if db.child('applicants').child(userid).get().val():
		category = 'applicants'	
	elif db.child('recruiters').child(userid).get().val():
		category = 'recruiters'
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

	if token != db.child(category).child(userid).child('login').child('token').get().val():
		return {'res': 2, 'msg': 'Mismatch Token'}
	elif time.time() > db.child(category).child(userid).child('login').child('expiration').get().val():
		return {'res': 3, 'msg': 'Session Expired'}

	applicant = db.child('applicants').child(targetid).get().val()
	if applicant:
		applicant.pop('login')
		applicant.pop('hashpw')
		applicant.pop('resume')
		applicant.pop('guest')
		
		if userid == targetid:
			if 'applications' not in applicant:
				applicant['applications'] = []
		else:
			if 'applications' in applicant:
				applicant['applications'] = len(applicant['applications'])
			else:
				applicant['applications'] = 0

		return {'res': 0, 'msg': 'Successful', 'applicant': applicant}
	else:
		return {'res': 4, 'msg': 'Target Not Found'}

# readRec 
@api.route('/readRec', methods = ['POST'])
def readRec():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	targetid = data.pop('targetid')

	if db.child('applicants').child(userid).get().val():
		category = 'applicants'
	elif db.child('recruiters').child(userid).get().val():
		category = 'recruiters'
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

	if token != db.child(category).child(userid).child('login').child('token').get().val():
		return {'res': 2, 'msg': 'Mismatch Token'}
	elif time.time() > db.child(category).child(userid).child('login').child('expiration').get().val():
		return {'res': 3, 'msg': 'Session Expired'}

	recruiter = db.child('recruiters').child(targetid).get().val()
	if recruiter:
		recruiter.pop('login')
		recruiter.pop('hashpw')

		if targetid == userid:
			if 'JDs' not in recruiter:
				recruiter['JDs'] = []
		else:
			if 'JDs' in recruiter:
				recruiter['JDs'] = len(recruiter['JDs'])
			else:
				recruiter['JDs'] = 0

		return {'res': 0, 'msg': 'Successful', 'recruiter': recruiter}
	else:
		return {'res': 4, 'msg': 'Target Not Found'}

# readJD
@api.route('/readJD', methods = ['POST'])
def readJD():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	jdid = data.pop('jdid')

	if db.child('applicants').child(userid).get().val():
		category = 'applicants'
	elif db.child('recruiters').child(userid).get().val():
		category = 'recruiters'
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

	if token != db.child(category).child(userid).child('login').child('token').get().val():
		return {'res': 2, 'msg': 'Mismatch Token'}
	elif time.time() > db.child(category).child(userid).child('login').child('expiration').get().val():
		return {'res': 3, 'msg': 'Session Expired'}

	JD = db.child('JDs').child(jdid).get().val()

	if JD:
		if JD['userid'] == userid:
			if 'applications' not in JD:
				JD['applications'] = []
		elif JD['status']['shown']:
			if 'applications' not in JD:
				JD['applications'] = 0
			else:
				JD['applications'] = len(JD['applications'])
		else:
			return {'res': 5, 'msg': 'JD Not Shown'}
		
		return {'res': 0, 'msg': 'Successful', 'JD': JD}
	else:
		return {'res': 4, 'msg': 'JD Does Not Exist'}


# updateJD
@api.route('/updateJD', methods = ['POST'])
def updateJD():
	data = request.form.to_dict()
	userid = data['userid']
	token = data.pop('token')

	data['shown'] = True if data['shown'] == 'true' else False
	data['available'] = True if data['available'] == 'true' else False
	data['status'] = {
		'shown': data.pop('shown', None),
		'available': data.pop('available', None),
	}
	
	data.pop('tag[]', None)
	data['tags'] = request.form.getlist('tag[]')
	
	data['workAuth'] = True if data['workAuth'] == 'true' else False	

	if db.child('recruiters').child(userid).get().val():
		if token != db.child('recruiters').child(userid).child('login').child('token').get().val():
			return {'res': 2, 'msg': 'Mismatch Token'}
		elif time.time() > db.child('recruiters').child(userid).child('login').child('expiration').get().val():
			return {'res': 3, 'msg': 'Session Expired'}
	elif db.child('applicants').child(userid).get().val():
		return {'res': 5, 'msg': 'Permission Denied: User is not a recruiter'}
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

	if 'jdid' in data and data['jdid'] != "": # if the jb exists and need update
		jdid = data.pop('jdid')

		JD = db.child('JDs').child(jdid).get().val()
		if JD:
			if JD['userid'] != userid: # user doesn't own the jb
				return {'res':4, 'msg': 'Permission Denied: User does not own this JD'}
			else:
				db.child('JDs').child(jdid).update(data)
				return {'res': 0, 'msg': 'Successful (update)'}
		else:
			return {'res': 6, 'msg': 'JD Not Exist'}
	else:
		data.pop('jdid', None)

		jdid = userid+'_'+''.join(random.choices(string.ascii_uppercase + string.digits, k = 16))
		data['releaseDate'] = date.today().strftime("%d/%m/%Y")
		data['applications'] = []
		db.child('JDs').child(jdid).set(data)
		
		JDs = db.child('recruiters').child(userid).child('JDs').get().val()
		if JDs:
			JDs.append(jdid)
			db.child('recruiters').child(userid).child('JDs').set(JDs)
		else:
			db.child('recruiters').child(userid).child('JDs').set([jdid])
		
		return {'res': 0, 'msg': 'Successful (create)'}


# submitApplication
@api.route('/submitApplication', methods = ['POST'])
def submitApplication():
	data = request.form.to_dict()
	userid = data['userid']
	token = data.pop('token')
	jdid = data['jdid']

	if db.child('applicants').child(userid).get().val():
		if token != db.child('applicants').child(userid).child('login').child('token').get().val():
			return {'res': 2, 'msg': 'Mismatch Token'}
		elif time.time() > db.child('applicants').child(userid).child('login').child('expiration').get().val():
			return {'res': 3, 'msg': 'Session Expired'}
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

	jd = db.child('JDs').child(jdid).get().val()
	if jd:
		if jd['status']['available']:
			appid = userid+'_'+''.join(random.choices(string.ascii_uppercase + string.digits, k = 16))
			
			data['starred'] = False
			data['timestamp'] = time.time()
			data['status'] = 'pending'

			db.child('applications').child(appid).set(data)
			
			apps = db.child('JDs').child(jdid).child('application').get().val()
			if apps:
				apps.append(appid)
				db.child('JDs').child(jdid).child('application').set(apps)
			else:
				db.child('JDs').child(jdid).child('application').set([appid])

			return {'res': 0, 'msg': 'Successful', 'appid': appid}
		else:
			return {'res': 4, 'msg': 'JD Not Exist'}
	else:
		return {'res': 5, 'msg': 'JD Not Exist'}


if __name__ == '__main__':
	api.run()