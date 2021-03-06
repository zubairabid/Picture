from app import db
from app import login
from flask_login import UserMixin
from datetime import datetime
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

likes = db.Table('likes',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    ncount = db.Column(db.Integer, default=0)

    posts = db.relationship('Post', cascade="all,delete", backref='author', lazy='dynamic')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    notifications = db.relationship('Notifications')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def user_posts(self):
        own = Post.query.filter_by(user_id=self.id)
        return own

    def like(self, post):
        if not self.liked(post):
            post.liked.append(self)

    def unlike(self, post):
        if self.liked(post):
            post.liked.remove(self)

    def liked(self, post):
        return post in self.likes

    def notify(self, notif, hreflink):
        n = Notifications()
        n.user_id = self.id
        n.notif = notif
        n.hreflink = hreflink
        print(hreflink + " " + n.hreflink)
        self.notifications.append(n)
        db.session.commit()

    def noti(self):
        return self.notifications[::-1]

    def ncountdown(self):
        if self.ncount > 0:
            self.ncount -= 1
            print("Reduced notification count for user to " + str(self.ncount))
            db.session.commit()
        return ''


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    imagelink = db.Column(db.String)
    body = db.Column(db.String(100000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship("Comment")

    liked = db.relationship(
        'User', secondary=likes,
        backref=db.backref('likes', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def comment(self, user, comment):
        commie = Comment()
        commie.comment = comment
        commie.user_id = user.id
        commie.post_id = self.id
        self.comments.append(commie)
        db.session.commit()


class Comment(db.Model):
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment = db.Column(db.String(100000))
    user = db.relationship("User")


class Notifications(db.Model):
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notif = db.Column(db.String(1000))
    hreflink = db.Column(db.String(1000))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
