import os

from flask import Flask, redirect, render_template, request, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from dotenv import load_dotenv

from processor import processor

load_dotenv()
# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_URI')
app.config['SECRET_KEY']= os.getenv('secret_key')
# initialize the app with the extension
db.init_app(app)

login_manager = LoginManager(app)

admin = Admin(app, name='name',template_mode='bootstrap3') # this gives an admin interface similar to Django.

#important functionality

UPLOAD_FOLDER = './static/process/' # folder to store the uploaded files
ALLOWED_EXTENSION = {'png','jpg','jpeg'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSION'] = ALLOWED_EXTENSION


#creating database
 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50), unique=True)
    password=db.Column(db.String(50),nullable=False)
    wallet = db.Column(db.Integer,default=0)
    hassubscription = db.Column(db.Boolean,default=0)

admin.add_view(ModelView(User,db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            user = User.query.filter_by(username=username).first()
            if user.password == password:
                login_user(user)
                flash('You are now logged in')
                return render_template('login.html')
            else:
                flash('wrong Password')
                return render_template('login.html')
        else:
            flash('This user does not exist')
    return render_template ('login.html')



@app.route('/process/', methods=['GET','POST'])
@login_required
def process():
    """
    The process view validates the extension of the uploaded file, if this is passed
    it then calls the processor function on the file. 
    """
    f = request.files['file']
    
    if f.filename == '':
        return render_template('image.html', message = 'Choose File')
    if f.filename.split('.')[1] in app.config['ALLOWED_EXTENSION']:
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],f.filename))
        processor(f.filename)
        return redirect(url_for('downloadgate',filename=f.filename))
    else:
        return redirect(url_for('image.html',message='Not an Image'))
        
@app.route('/image')
@login_required
def image():
    return render_template('image.html',message='Choose an image')


@app.route('/downloadgate/<filename>')
@login_required
def downloadgate(filename):
    """
    This view function initiates a payment gateway were the current users wallet 
    is checked for enough balance and if true returns the downloadgate.html page which redirects to the download route.
    """
    if current_user.hassubscription:
        return redirect(url_for('download', filename=filename))

    if int(current_user.wallet) > 15:
        message = '1 process costs 15 Pounds, click the download link to continue.'
        return render_template('downloadgate.html', filename=filename, message = message)
    else:
        return render_template('deposit.html')  

          
@app.route('/download/<filename>')
@login_required
def download(filename):
    if current_user.hassubscription:
        filelocation = './static/process/'+filename
        return send_file(filelocation,as_attachment=True)

    newwalletamount = int(current_user.wallet) - 15
    current_user.wallet = newwalletamount
    db.session.commit()
    filelocation = './static/process/'+filename
    return send_file(filelocation,as_attachment=True)

@app.route('/deposit/', methods = ['POST','GET'])
def deposit():
    return render_template('deposit.html')


@app.route('/deposit/success/',methods=['POST','GET'])
def depositsuccessfull():
    value = request.form.get('amount')
    print(value)
    if value:
        amount = value
        print(amount)
        newwalletamount = int(current_user.wallet) + int(amount)
        current_user.wallet = newwalletamount
        db.session.commit()
    return redirect(url_for('home'))


@login_required
def deposit():
    return render_template('deposit.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()   
    return render_template('index.html')
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5002)