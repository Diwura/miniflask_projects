import os
import datetime
from functools import wraps
 
from flask import Flask, jsonify,request,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from werkzeug.security import generate_password_hash, check_password_hash

import uuid
import jwt
from dotenv import load_dotenv



app = Flask(__name__)

load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('SQLALCHEMY_URI')
app.config['SECRET_KEY'] = os.getenv('secret_key')

db = SQLAlchemy(app)

admin = Admin(app, name='name',template_mode='bootstrap3')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50),nullable=False)
    admin = db.Column(db.Boolean, default = False)
    
admin.add_view(ModelView(User,db.session))

with app.app_context():
    db.create_all()

def createuser(username):
    password = 'boss'
    hashedpassword= generate_password_hash(password,method='sha256')
    new_user = User(
        public_id = str(uuid.uuid4()),
        username= username,
        password=hashedpassword
    )
    db.session.add(new_user)
    db.session.commit()
    
def token_required(f):
    """
    This is a decorator function that checks 
     for a valid token before allowing a request to be processed. 
     It first checks if the token exists in the request headers 
     and if it does, it verifies the token using the app's secret key stored in the configuration. 
     If the token is valid, the function continues to process the request. If the 
    token doesn't exist or is invalid, the decorator returns an error response.
    """
    @wraps(f)
    def decorated(*args,**kwargs):
        token =None
        if 'x-access-token' in request.headers:
            token = request. headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing'}),401
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args,**kwargs)
    return decorated


@app.route('/data')
@token_required
def getdata(current_user):
    return jsonify({'data':'topsecuredata'})

@app.route('/api/login')
def login():
    """
    The login func uses the make_response func to request authentication details from the user
    then verifies the details using the check_password_hash function 
    """
    auth = request.authorization
    if not auth or not auth. username or not auth.password:
        return make_response('Could not veriy',401,{'WWW-Authenticate':'Basic realm="Login required!"'})
    
    user = User.query.filter_by(username = auth.username).first()
    
    if not user:
        return make_response('Could not veriy',401,{'WWW-Authenticate':'Basic realm="Login required!"'})
    
    elif check_password_hash(user.password, auth.password):
        token =  jwt.encode({'public_id':user.public_id,'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=30)}
                            ,app.config['SECRET_KEY'])
        print(token)
        return jsonify({'token':token.decode('utf-8')})
    
    
    return make_response('Could not veriy',401,{'WWW-Authenticate':'Basic realm="Login required!"'})

if __name__ == '__main__':
   app.run(debug=True, port=5003)
    