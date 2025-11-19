from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

bcrypt = Bcrypt()
auth = Blueprint('auth', __name__)

# ✅ Kết nối MongoDB
client = MongoClient("mongodb+srv://MyFinance_db_user:MyFinaNceWebsite@cluster0.2z74lfk.mongodb.net/")
db = client["expense_tracker"]
users = db["users"]

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if users.find_one({'email': email}):
            flash("Email đã tồn tại!")
            return redirect(url_for('auth.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        users.insert_one({'name': name, 'email': email, 'password': hashed_pw})
        flash("Đăng ký thành công! Vui lòng đăng nhập.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            flash("Đăng nhập thành công!")
            return redirect(url_for('index'))
        else:
            flash("Sai email hoặc mật khẩu!")

    return render_template('login.html')


@auth.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.")
    return redirect(url_for('auth.login'))

@auth.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('settings.html')
