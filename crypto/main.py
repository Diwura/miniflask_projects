import os 

from flask import Flask, redirect, render_template, request, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from bit import PrivateKey
from dotenv import load_dotenv



# create the app
app = Flask(__name__)
load_dotenv()
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_URI')
app.config['SECRET_KEY']= os.getenv('secrety_key')
app.config['TRANSACTION_PERCENTAGE'] = 5
app.config['COMPANY_ADDRESS']='1L3Zx61xMLoHK3EQNSUMGUrhGFU3wsM72h'
# initialize the app with the extension
db = SQLAlchemy(app)

login_manager = LoginManager(app)

admin = Admin(app, name='name',template_mode='bootstrap3')



#creating database
 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50), unique=True)
    password=db.Column(db.String(50),nullable=False)
    wallet = db.Column(db.String(1000), nullable=False)
    address = db.Column(db.String(100), nullable = False)
    amount = db.Column(db.String(1000),default = 0)
    email = db.Column(db.String(1000), nullable=False)


admin.add_view(ModelView(User,db.session))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def getbalance(wallet):
    key = PrivateKey(wallet) #this imports a private key in wallet import format directly to the initializer
    newbalance = key.balance_as('usd')
    user = User.query.filter_by(wallet=wallet)
    user.amount = newbalance
    db.session.commit()

@app.route('/')
def home():
    getbalance(current_user.wallet)
    return render_template('index.html')


@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'POST' and request.form.get('username') and request.form.get('password') and request.form.get('email'):
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('email is already registered, try another email or login if email belongs to you.')
            return render_template('signup.html')
        else:
            wallet = PrivateKey()
            user = User(username=username,email=email, password=password,address=wallet.address, 
            wallet=wallet.to_wif()) #the wallet.to_wif() helps to export the privatekey which is used for transaction.
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
            
    elif request.method == 'POST':
        flash("Check your input")
        
    else:
        return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            user = User.query.filter_by(username=username).first()
            if user.password == password:
                login_user(user)
                flash('You are now logged in')
                return redirect(url_for('home'))
            else:
                flash('wrong Password')
                return render_template('login.html')
        else:
            flash('This user does not exist')
            return render_template ('login.html')

    return render_template('login.html')


@app.route('/createtransaction',methods=['POST','GET'])  
@login_required
def transact():
    getbalance(current_user.wallet)
    if request.method == 'POST' and request.form.get('address') and request.form.get('amount'):
        address = request.form.get('address')
        amount = request.form.get('amount')
        if int(current_user.wallet) < int(amount):
            flash("not enough money in wallet for this transaction")
            return render_template('transact.html')
        key = PrivateKey(current_user.wallet)
        myamount = (app.config['Transaction_Percentage']/100)*amount
        youramount = amount-myamount 
        (app.config['Transaction_Percentage']/100)*amount
        transactionid = key.send([(address, youramount,'usd'),(app.config['COMPANY_ADDRESS'],myamount,'usd')])
        flash(f'Transaction Completed + transaction id is: {transactionid}')
        return render_template('transact.html')
    return render_template('transact.html')

        

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