# Stores all the URL actions. Divided into 3 major classes -
# 1. Utility Functions
# 2. Actions: upload, unregister, etc

import os
from app import app, db, photos
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, UnregistrationForm
from app.models import User, Post, Comment
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from app.custom import tagger


# sets the last seen. Updates before every request made by the user
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# Feed pages
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/explore')
@login_required # TODO hopefully temp  until someshit fixed
def explore():
    print(current_user)
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)

# User pages
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/post/<pid>')
@login_required
def post(pid):
    post = Post.query.filter_by(id=pid).first_or_404()
    return render_template('post.html', post=post)

@app.route('/notifications')
@login_required
def notifications(user_id):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return redirect(url_for('index'))

    user.ncount = 0
    return None

# User actions - photo upload, profile edit, etc
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = PostForm()
    if form.validate_on_submit():
        image = form.photo.data
        filename = photos.save(image)
        file_url = photos.url(filename)
        post = Post(body=tagger(form.caption.data), imagelink=file_url ,author = current_user)
        db.session.add(post)
        db.session.commit()
        flash('Uploaded your image!')
        return redirect(url_for('index'))

    return render_template('upload.html', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = tagger(form.about_me.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)




@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)

    user.ncount = (user.ncount or 0) + 1
    link = url_for('user', username=current_user.username)
    print(link)
    user.notify(notif=(current_user.username + ' has followed you!'), hreflink=link)

    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/comment', methods=['POST'])
@login_required
def comment():
    pid = request.form.get("post_id")
    post = Post.query.filter_by(id = pid).first()
    if post is None:
        flash("Post not found")
        return redirect(url_for('index'))

    text = request.form.get("comment") or "generic comment text"
    text = tagger(text)
    post.comment(current_user, text)

    user = User.query.filter_by(id=post.user_id).first()
    user.ncount = user.ncount + 1
    link = url_for('post', pid=pid)
    print(link)
    user.notify(notif=(current_user.username + ' has commented on your post'), hreflink=link)

    db.session.commit()
    return jsonify(user = current_user.username, comment = text)

@app.route('/uncomment/<cid>', methods=['GET', 'POST'])
@login_required
def uncomment(cid):
    comment = Comment.query.filter_by(timestamp=cid).first()
    if comment is None:
        flash("Comment not found")
        return redirect(url_for('index'))

    if comment.user_id != current_user.id:
        return redirect(url_for('index'))

    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/unpost/<pid>', methods=['GET', 'POST'])
@login_required
def unpost(pid):
    post = Post.query.filter_by(id = pid).first()
    if post is None:
        flash("Post not found")
        return redirect(url_for('index'))

    if post.user_id != current_user.id:
        return redirect(url_for('index'))

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/like', methods=['POST'])
@login_required
def like():
    pid = request.form.get("post_id")
    post = Post.query.filter_by(id = pid).first()
    if post is None:
        flash("Post not found")
        return redirect(url_for('index'))
    current_user.like(post)

    user = User.query.filter_by(id=post.user_id).first()
    print("Post user found : " + str(user.id))
    user.ncount = (user.ncount or 0) + 1
    link = url_for('post', pid=pid)
    print(link)
    user.notify(notif=(current_user.username + ' has liked your post'), hreflink=link)

    db.session.commit()
    return jsonify(result=(str(post.liked.count()) + " Unlike"))

@app.route('/unlike', methods=['POST'])
@login_required
def unlike():
    pid = request.form.get("post_id")
    post = Post.query.filter_by(id = pid).first()
    if post is None:
        flash("Post not found")
        return redirect(url_for('index'))
    current_user.unlike(post)
    db.session.commit()
    return jsonify(result=(str(post.liked.count()) + " Like"))


# Logins and user management
@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('login'))
		login_user(user, remember = form.remember_me.data)

		next_page = request.args.get('next')
		print(next_page)
		print(type(next_page))
		# print(type(url_parse(next_page)))
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)

	return render_template('/login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/unregister', methods=['GET', 'POST'])
def unregister():
    if not (current_user.is_authenticated):
        return redirect(url_for('index'))

    form = UnregistrationForm()
    if form.validate_on_submit():
        # yes

        for user in current_user.followed.all():
            current_user.unfollow(user)

        for comment in Comment.query.all():
            if comment.user_id == current_user.id:
                db.session.delete(comment)

        db.session.commit()
        db.session.delete(current_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('unregister.html', title='Unregister', form=form)

@app.route('/searchrun/', methods=['GET', 'POST'])
def search():

    if request.method == 'POST':

        name = request.form.get('Search')
        print('search: got name ' + str(name))
        userlist = []
        allu = User.query.all()
        for u in allu:
            if str(name) in u.username:
                userlist.append(u)
                print('appended ' + str(u) + ' to userlist')

        if len(userlist) == 0:
            return render_template('search.html')
        else:
            return render_template('searchperson.html', users=userlist)

    return render_template('search.html')
