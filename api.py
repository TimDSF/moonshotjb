import base64
import bcrypt
import glob
import os
import random
import string
import sys
import time

from affinda import AffindaAPI, TokenCredential
from datetime import date
from db import db, st, firebase
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

UPLOAD_FOLDER = './uploads'
MAX_SIZE = 10240 # in bytes
ALLOWED_FORMATS_RESUME = {'pdf', 'txt', 'doc', 'docx'}
ALLOWED_FORMATS_LOGO = {'jpg', 'jpeg', 'png'}

AffindaToken = '15197965097a1f10ac9cdcb75334b88feef21c84'
AffindaCred = TokenCredential(token = AffindaToken)
AffindaClient = AffindaAPI(credential = AffindaCred)

api = Flask(__name__)
api.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api.config['MAX_CONTENT_PATH'] = MAX_SIZE

def login(userid, token, allowed_category):
	if db.child('applicants').child(userid).get().val():
		category = 'applicants'	
	elif db.child('recruiters').child(userid).get().val():
		category = 'recruiters'
	else:
		return {'res': 1, 'msg': 'User Not Registered'}

	if category not in allowed_category:
		return {'res': 4, 'msg': 'Permission Denied'}

	if token != db.child(category).child(userid).child('login').child('token').get().val():
		return {'res': 2, 'msg': 'Mismatch Token'}
	elif time.time() > db.child(category).child(userid).child('login').child('expiration').get().val():
		return {'res': 3, 'msg': 'Session Expired'}

	return {'res': 0, 'msg': 'Successful', 'category': category}

# /
@api.route('/', methods = ['GET'])
def test():
    return '''
    <h1> Successful </h1>
    <p> @ River, Tim, Victor, Frank </p>
    <p> !! Special thanks to Daniel </p>
    <p> &copy; MoonShot Job Board 2022 </p>
    '''

# console
@api.route('/console', methods = ['GET'])
def console():
	file = max(glob.glob('./log/*.log'))
	log = open(file).read().replace('\n', '<br>')
	return '<meta http-equiv="refresh" content="30" />' + log

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
		return {'res': 1, 'msg': 'Username Not Registrated As An Applicant'}

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
		return {'res': 1, 'msg': 'Username Not Registrated As A Recruiter'}

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
@api.route('/updateApp', methods = ['POST'])
def updateApp():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')

	res = login(userid, token, ['applicants'])
	if res['res']:
		return res
	
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

	db.child('applicants').child(userid).update(data)

	return {'res': 0, 'msg': 'Successful'}

# upload resume
@api.route('/uploadResume', methods = ['POST'])
def uploadResume():	
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')

	res = login(userid, token, ['applicants'])
	if res['res']:
		return res

	if 'resume' in request.files:
		file = request.files['resume']
		extension = file.filename.split('.')[-1].lower()
		filename = 'resume_'+userid+'.'+extension

		if not file or file.filename == '':
			return {'res': 5, 'msg': 'No Resume Uploaded'}
		elif extension not in ALLOWED_FORMATS_RESUME:
			return {'res': 6, 'msg': 'Unsupported Resume Format'}
		else:
			filename_ = 'resume_'+userid+'.*'
			path_ = os.path.join(UPLOAD_FOLDER, filename_)
			for path in glob.glob(path_):
				os.remove(path)

			path = os.path.join(UPLOAD_FOLDER, filename)
			file.save(path)
	else:
		return {'res': 5, 'msg': 'No Resume Uploaded'}

	file2 = open(path, 'rb')
	resume = AffindaClient.create_resume(file = file2)

	skills = resume.as_dict()['data']['skills']
	tags = [''] * len(skills)
	for idx, tmp in enumerate(skills):
		tags[idx] = tmp['name']

	return {'res': 0, 'msg': 'Successful', 'tags': tags}

# download resume
@api.route('/downloadResume', methods = ['POST'])
def downloadResume():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	targetid = data.pop('targetid')
	
	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

	category = res['category']
	if category == 'applicants' and userid != targetid:
		return {'res': 4, 'msg': 'Permission Denied'}

	filename = 'resume_'+targetid+'.*'
	paths = glob.glob(os.path.join(UPLOAD_FOLDER, filename))

	if len(paths) == 0:
		return {'res': 5, 'msg': 'Resume Not Uploaded'}

	filename = paths[0].split('/')[-1]

	return send_from_directory(directory = UPLOAD_FOLDER, path = filename, filename = filename)

# upload logo
@api.route('/uploadLogo', methods = ['POST'])
def uploadLogo():	
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')

	res = login(userid, token, ['recruiters'])
	if res['res']:
		return res

	if 'logo' in request.files:
		file = request.files['logo']
		extension = file.filename.split('.')[-1].lower()
		filename = 'logo_'+userid+'.'+extension

		if not file or file.filename == '':
			return {'res': 5, 'msg': 'No Logo Uploaded'}
		elif extension not in ALLOWED_FORMATS_LOGO:
			return {'res': 6, 'msg': 'Unsupported Logo Format'}
		else:
			filename_ = 'logo_'+userid+'.*'
			path_ = '/home/ec2-user/public_html/moonshotjb/logos/' + filename_
			for path in glob.glob(path_):
				os.remove(path)

			path = '/home/ec2-user/public_html/moonshotjb/logos/' + filename
			file.save(path)
	else:
		return {'res': 5, 'msg': 'No Logo Uploaded'}

	return {'res': 0, 'msg': 'Successful'}


# download logo
@api.route('/downloadLogo', methods = ['POST'])
def downloadLogo():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	targetid = data.pop('targetid')

	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

	paths = glob.glob('/home/ec2-user/public_html/moonshotjb/logos/logo_'+targetid+'.*')

	if len(paths) == 0:
		return {'res': 5, 'msg': 'Logo Not Uploaded'}
	path = 'http://ec2-52-14-66-91.us-east-2.compute.amazonaws.com/~ec2-user/moonshotjb/logos/' + paths[0].split('/')[-1]
	return {'res': 0, 'msg': 'Successful', 'logourl': path}


# update recruiter
@api.route('/updateRec', methods = ['POST'])
def updateRec():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')

	res = login(userid, token, ['recruiters'])
	if res['res']:
		return res

	data['verified'] = False
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

	db.child('recruiters').child(userid).update(data)

	return {'res': 0, 'msg': 'Successful'}
	
# readApp 
@api.route('/readApp', methods = ['POST'])
def readApp():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	targetid = data.pop('targetid')

	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

	applicant = db.child('applicants').child(targetid).get().val()
	if applicant:
		applicant.pop('login')
		applicant.pop('hashpw')
		applicant.pop('guest')
		
		if userid == targetid:
			if 'applications' not in applicant:
				applicant['applications'] = []

			for idx, appid in enumerate(applicant['applications']):
				app = db.child('applications').child(appid).get().val()
				JD = db.child('JDs').child(app['jdid']).get().val()
				JD['applications'] = len(JD['applications'])

				applicant['applications'][idx] = {'app': app, 'JD': JD}
		else:
			if 'applications' in applicant:
				applicant['applications'] = len(applicant['applications'])
			else:
				applicant['applications'] = 0

		return {'res': 0, 'msg': 'Successful', 'applicant': applicant}
	else:
		return {'res': 5, 'msg': 'Target Not Found'}


# readRec 
@api.route('/readRec', methods = ['POST'])
def readRec():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	targetid = data.pop('targetid')

	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

	recruiter = db.child('recruiters').child(targetid).get().val()
	if recruiter:
		recruiter.pop('login')
		recruiter.pop('hashpw')

		if 'JDs' not in recruiter:
			recruiter['JDs'] = []

		dels = []
		for idx, jdid in enumerate(recruiter['JDs']):
			JD = db.child('JDs').child(jdid).get().val()
			if JD and JD['status']['shown']:
				JD.pop('userid')
				JD['jdid'] = jdid
				recruiter['JDs'][idx] = JD
			else:
				dels.append(idx)

		recruiter['JDs'] = [recruiter['JDs'][idx] for idx in range(len(recruiter['JDs'])) if idx not in dels]

		return {'res': 0, 'msg': 'Successful', 'recruiter': recruiter}
	else:
		return {'res': 5, 'msg': 'Target Not Found'}

# getRecommendationJD
@api.route('/getRecommendationJD', methods = ['POST'])
def getRecommendationJD():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')

	guest = userid == '' and token == ''
	if not guest:
		res = login(userid, token, ['applicants'])

		if res['res']:
			if res['res'] != 3:
				return res
	
	if userid:
		tags = db.child('applicants').child(userid).child('tags').get().val()
	else:
		tags = []
	if not tags:
		tags = []
	tags = set(tags)
		
	if userid:
		apps = db.child('applicants').child(userid).child('applications').get().val()
	else:
		apps = []
	if not apps:
		apps = []

	JDs = dict(db.child('JDs').get().val())
	dels = [jdid for jdid in JDs if not (jdid not in apps and JDs[jdid]['status']['shown'] and JDs[jdid]['status']['available'])]

	for jdid in dels:
		del JDs[jdid]

	for jdid in JDs:
		if 'tags' in JDs[jdid]:
			JDTags = JDs[jdid]['tags']
		else:
			JDTags = []
		JDTags = set(JDTags)

		JDs[jdid]['score'] = len(tags & JDTags)
		JDs[jdid]['jdid'] = jdid
		if 'applications' in JDs[jdid]:
			JDs[jdid]['applications'] = len(JDs[jdid]['applications'])
		else:
			JDs[jdid]['applications'] = 0

	recommendations = sorted(list(JDs.values()), key = lambda x: x['score'], reverse = True)
	return {'res': res['res'], 'msg': 'Successful', 'JDs': recommendations}

# readJD
@api.route('/readJD', methods = ['POST'])
def readJD():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	jdid = data.pop('jdid')

	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

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
		return {'res': 6, 'msg': 'JD Does Not Exist'}


# updateJD
@api.route('/updateJD', methods = ['POST'])
def updateJD():
	data = request.form.to_dict()
	userid = data['userid']
	token = data.pop('token')

	res = login(userid, token, ['recruiters'])
	if res['res']:
		return res

	data['shown'] = True if data['shown'] == 'true' else False
	data['available'] = True if data['available'] == 'true' else False
	data['status'] = {
		'shown': data.pop('shown', None),
		'available': data.pop('available', None),
	}
	
	data.pop('tag[]', None)
	data['tags'] = request.form.getlist('tag[]')
	
	data['workAuth'] = True if data['workAuth'] == 'true' else False	

	if 'jdid' in data and data['jdid'] != "": # if the jb exists and need update
		jdid = data.pop('jdid')

		JD = db.child('JDs').child(jdid).get().val()
		if JD:
			if JD['userid'] != userid: # user doesn't own the jb
				return {'res':4, 'msg': 'Permission Denied: User does not own this JD'}
			else:
				db.child('JDs').child(jdid).update(data)
		else:
			return {'res': 6, 'msg': 'JD Not Exist'}
	else:
		data.pop('jdid', None)

		jdid = userid+'_'+str(int(time.time()*1000))
		data['releaseDate'] = date.today().strftime("%d/%m/%Y")
		data['applications'] = []
		db.child('JDs').child(jdid).set(data)
		
		JDs = db.child('recruiters').child(userid).child('JDs').get().val()
		if JDs:
			JDs.append(jdid)
			db.child('recruiters').child(userid).child('JDs').set(JDs)
		else:
			db.child('recruiters').child(userid).child('JDs').set([jdid])
		
	desc = data['description']
	path = 'tmp'+str(time.time())+'.txt'
	f = open(path, 'w')
	f.write(desc)
	f.close()

	f = open(path, 'rb')
	resume = AffindaClient.create_resume(file = f)
	f.close()

	os.remove(path)

	skills = resume.as_dict()['data']['skills']
	tags = [''] * len(skills)
	for idx, tmp in enumerate(skills):
		tags[idx] = tmp['name']

	return {'res': 0, 'msg': 'Successful', 'tags': tags}

# removeJD
@api.route('/removeJD', methods = ['POST'])
def removeJD():
	data = request.form.to_dict()
	userid = data['userid']
	token = data.pop('token')

	res = login(userid, token, ['recruiters'])
	if res['res']:
		return res

	jdid = data.pop('jdid')

	JD = db.child('JDs').child(jdid).get().val()
	if JD:
		if JD['userid'] != userid: # user doesn't own the jb
			return {'res':4, 'msg': 'Permission Denied: User does not own this JD'}
		else:
			appids = db.child('JDs').child(jdid).child('applications').get().val()
			db.child('JDs').child(jdid).remove()

			JDs = db.child('recruiters').child(userid).child('JDs').get().val()
			if jdid in JDs:
				JDs.remove(jdid)
			db.child('recruiters').child(userid).child('JDs').set(JDs)

			for appid in appids:
				db.child('applications').child(appid).remove()

				userid = appid[:-(len(jdid)+1)]
				apps = db.child('applicants').child(userid).child('applications').get().val()
				if appid in apps:
					apps.remove(appid)
				db.child('applicants').child(userid).child('applications').set(apps)


	else:
		return {'res': 5, 'msg': 'JD Not Exist'}

	return {'res': 0, 'msg': 'Successful'}


# submitApplication
@api.route('/submitApplication', methods = ['POST'])
def submitApplication():
	data = request.form.to_dict()
	userid = data['userid']
	token = data.pop('token')
	jdid = data['jdid']

	res = login(userid, token, ['applicants'])
	if res['res']:
		return res

	jd = db.child('JDs').child(jdid).get().val()
	if jd:
		if jd['status']['available']:
			apps = db.child('applicants').child(userid).child('applications').get().val()
			appid = userid+'_'+jdid
			
			if not apps or appid not in apps:
				
				data['starred'] = False
				data['timestamp'] = time.time()
				data['status'] = 'pending'

				db.child('applications').child(appid).set(data)
				
				apps = db.child('JDs').child(jdid).child('applications').get().val()
				if apps:
					apps.append(appid)
					db.child('JDs').child(jdid).child('applications').set(apps)
				else:
					db.child('JDs').child(jdid).child('applications').set([appid])

				apps = db.child('applicants').child(userid).child('applications').get().val()
				if apps:
					apps.append(appid)
					db.child('applicants').child(userid).child('applications').set(apps)
				else:
					db.child('applicants').child(userid).child('applications').set([appid])

				return {'res': 0, 'msg': 'Successful', 'appid': appid}
			else:
				return {'res': 6, 'msg': 'Already Applied'}
		else:
			return {'res': 7, 'msg': 'JD Not Available'}
	else:
		return {'res': 5, 'msg': 'JD Not Exist'}


# viewApplication
@api.route('/viewApplication', methods = ['POST'])
def viewApplication():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	appid = data.pop('appid')

	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

	category = res['category']

	app = db.child('applications').child(appid).get().val()
	if app:
		if category == 'applicants':
			if app['userid'] == userid:
				return {'res': 0, 'msg': 'Successful', 'application': app}
			else:
				return {'res': 5, 'msg': 'Permission Denied: Application Not Yours'}
		else:
			JDs = db.child('recruiters').child(userid).child('JDs').get().val()
			if JDs and app['jdid'] in JDs:
				if app['status'] == 'withdrawn':
					return {'res': 7, 'msg': 'Application Withdrawn'}
				else:
					return {'res': 0, 'msg': 'Successful', 'application': app}
			else:
				return {'res': 6, 'msg': 'Permission Denied: JD Not Yours'}
	else:
		return {'res': 8, 'msg': 'Application Not Exist'}

# updateApplication
@api.route('/updateApplication', methods = ['POST'])
def updateApplication():
	data = request.form.to_dict()
	userid = data.pop('userid')
	token = data.pop('token')
	appid = data.pop('appid')
	status = data.pop('status')

	res = login(userid, token, ['applicants', 'recruiters'])
	if res['res']:
		return res

	category = res['category']

	app = db.child('applications').child(appid).get().val()
	if not app:
		return {'res': 5, 'msg': 'Application Not Exist'}

	if category == 'recruiters':
		if app['status'] != 'pending' or status not in ['accepted', 'rejected'] or userid != db.child('JDs').child(app['jdid']).child('userid').get().val():
			return {'res': 4, 'msg': 'Permission Deinied'}
	else:
		apps = db.child('applicants').child(userid).child('applications').get().val()
		if app['status'] != 'pending' or status not in ['withdrawn'] or not apps or appid not in apps:
			return {'res': 4, 'msg': 'Permission Deinied'}

	db.child('applications').child(appid).child('status').set(status)

	return {'res': 0, 'msg': 'Successful'}	
    

if __name__ == '__main__':
	api.run(port = 5000, host = '0.0.0.0')
