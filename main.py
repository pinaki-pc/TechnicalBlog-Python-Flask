import json
import datetime
import math
import os
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename


local_server = True

# this import for avoid mysqldb error--------

import pymysql

pymysql.install_as_MySQLdb()
# --------------------------------------------

# opening json file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['mail_user'],
    MAIL_PASSWORD=params['mail_pass']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Cntact(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    mess = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    p_title = db.Column(db.String(80), nullable=False)
    p_subtitle = db.Column(db.String(20), nullable=False)
    p_desc = db.Column(db.String(120), nullable=False)
    p_slug = db.Column(db.String(21), nullable=False)
    p_author = db.Column(db.String(21), nullable=False)
    p_date = db.Column(db.String(12), nullable=False)
    p_img = db.Column(db.String(21), nullable=False)



@app.route("/")
def home():
    post = Post.query.filter_by().all()
    last = math.ceil(len(post) /int(params['show_posts']))
    # [0:params['show_posts']]
    page=request.args.get('page')
    if  (not str(page).isnumeric()):
        page=1
    page=int(page)
    post=post[(page-1)*int(params['show_posts']):(page-1)*int(params['show_posts'])+int(params['show_posts'])]

    if (page ==1):
        prev ="#"
        next="/?page="+str(page+1)
    elif(page == last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html', params=params, post=post,prev=prev,next=next)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
        post = Post.query.all()
        return render_template('dashboard.html', params=params, post=post)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('pass')
        if (username == params['admin_username'] and password == params['admin_pass']):
            session['user'] = username
            post = Post.query.all()
            return render_template('dashboard.html', params=params, post=post)
    return render_template('adminlogin.html', params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    post = Post.query.filter_by(sno=sno).first()
    db.session.delete(post)
    db.session.commit()
    return redirect('/dashboard')

@app.route("/search", methods=['GET', 'POST'])
def search():
    if (request.method == 'POST'):
        s = request.form.get('search')
        posts = Post.query.filter_by(sno=s).first()
        return render_template('search.html', params=params)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_username']):
        if (request.method == 'POST'):
            f = request.files['fileToUpload']
            id = request.form.get('slno')
            if (f.filename!='' and id!= ''):
                f.save(os.path.join(app.config['UPLOAD_FOLDER'] , secure_filename(f.filename)))
                post = Post.query.filter_by(sno=id).first()
                post.p_img = f.filename
                db.session.commit()

                res_msg_true = params['b_success']
                post = Post.query.all()
                return render_template('dashboard.html', params=params, msg=res_msg_true, post=post, text=params['res_msg_true'])
            else:
                res_msg_false = params['b_danger']
                post = Post.query.all()
                return render_template('dashboard.html', params=params, msg=res_msg_false, post=post, text=params['res_msg_false'])



@app.route("/newpost/<string:nsno>", methods=['GET', 'POST'])
def newpost(nsno):
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method == 'POST':
            p_title = request.form.get('title')
            p_subtitle = request.form.get('tagline')
            p_desc = request.form.get('content')
            p_slug = request.form.get('slug')
            p_author = request.form.get('author')
            p_date = datetime.datetime.now()
            p_img = request.form.get('image')

            post = Post(p_title=p_title, p_subtitle=p_subtitle, p_desc=p_desc, p_slug=p_slug, p_date=p_date, p_author=p_author, p_img=p_img)
            db.session.add(post)
            db.session.commit()
        post = Post.query.filter_by(sno=nsno).first()
        return render_template('newpost.html', params=params, post=post)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method == 'POST':
            p_title = request.form.get('title')
            p_subtitle = request.form.get('tagline')
            p_desc = request.form.get('content')
            p_slug = request.form.get('slug')
            p_author = request.form.get('author')
            p_date = datetime.datetime.now()
            p_img = request.form.get('image')

            if sno == '0':
                post = Post(p_title=p_title, p_subtitle=p_subtitle, p_desc=p_desc, p_slug=p_slug, p_date=p_date,
                            p_author=p_author, p_img=p_img)
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.p_title = p_title
                post.p_subtitle = p_subtitle
                post.p_desc = p_desc
                post.p_slug = p_slug
                post.p_date = p_date
                post.p_author = p_author
                post.p_img = p_img
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)
    else:
        return render_template('adminlogin.html', params=params)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        msg = request.form.get('message')
        emails = request.form.get('email')
        date = datetime.datetime.now()
        #   insert into database
        entry = Cntact(name=name, email=emails, phone=phone, mess=msg, date=date)
        db.session.add(entry)
        db.session.commit()
        # sending mail using smtp:465
        mail.send_message('New message from blog - ' + name,
                          sender=emails,
                          recipients=[params['mail_user']],
                          body=msg + "\n Contact - " + phone
                          )
    return render_template('contact.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(p_slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


app.run(debug=True)
