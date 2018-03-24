import flask_dance
from flask import Flask, render_template, abort, flash, url_for, redirect, request
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.backend.sqla import SQLAlchemyBackend
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm.exc import NoResultFound
from wtforms import StringField
from wtforms.validators import DataRequired
from models import Category, Item, User, db, OAuth
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.config.from_object('config')
app.url_map.strict_slashes = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

google_bp = make_google_blueprint(
    client_id="105968859277-16r4kkuv356r2bdfgtqf85nidq2r1hgo.apps.googleusercontent.com",
    client_secret="xs0vSUb2n0KMb1DMPph1KFhO",
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")
google_bp.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])


@app.route('/')
def index():
    return render_template('home.html',
                           categories=Category.query.all(),
                           latest_items=Item.query.order_by(Item.created_at.desc()),
                           )


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    # Login and validate the user.
    if form.validate_on_submit():
        login_user(User.query.filter(User.username == form.username.data).first())

        flash('Logged in successfully.')

        return redirect(request.args.get('next') or url_for('index'))
    print(form.errors)
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('index')


@app.route('/categories/<string:category>')
def get_category(category):
    category = Category.query.filter(Category.name == category).first()
    return render_template('category.html',
                           categories=Category.query.all(),
                           category=category,
                           items=Item.query.filter(Item.category_id == category.id)
                           )


@app.route('/categories/<string:category>/<string:item>')
def get_item(category, item):
    item = Item.query.join(Item.category).filter(Item.name == item).filter(Category.name == category).first()
    if item is None:
        abort(404)

    return render_template('items/item.html',
                           category=category,
                           item=item
                           )


@app.route('/categories/<string:category>/<string:item>/edit', methods=['GET', 'POST'])
def edit_item(category, item):
    item = Item.query.join(Item.category).filter(Item.name == item).filter(Category.name == category).first()
    if item is None:
        abort(404)

    return render_template('items/edit.html',
                           category=category,
                           item=item
                           )


@app.route('/categories/<string:category>/<string:item>/delete', methods=['GET', 'POST'])
def delete_item(category, item):
    item = Item.query.join(Item.category).filter(Item.name == item).filter(Category.name == category).first()
    if item is None:
        abort(404)

    if request.method == 'POST':
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('items/delete.html',
                           category=category,
                           item=item
                           )


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with Google.", category="error")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        msg = "Failed to fetch user info from Google."
        flash(msg, category="error")
        return False

    google_info = resp.json()
    google_id = google_info['id']

    print(google_info)

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider=blueprint.name,
        provider_user_id=google_id,
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(
            provider=blueprint.name,
            provider_user_id=google_id,
            token=token,
        )

    if oauth.user:
        # If this OAuth token already has an associated local account,
        # log in that local user account.
        # Note that if we just created this OAuth token, then it can't
        # have an associated local account yet.
        login_user(oauth.user)
    else:
        # If this OAuth token doesn't have an associated local account,
        # create a new local user account for this user. We can log
        # in that account as well, while we're at it.
        user = User(
            # Remember that `email` can be None, if the user declines
            # to publish their email address on GitHub!
            email=google_info["email"],
            name=google_info["name"],
            username=google_info['email']
        )
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        login_user(user)
    flash("Successfully signed in with Google.")

    # Disable Flask-Dance's default behavior for saving the OAuth token
    return False


if __name__ == '__main__':
    app.run()
