from flask import Flask, render_template, flash, url_for, redirect, request
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.backend.sqla import SQLAlchemyBackend
from flask_dance.contrib.google import make_google_blueprint
from flask_login import LoginManager, login_user, login_required, \
    logout_user, current_user
from flask_wtf import CSRFProtect, FlaskForm
from sqlalchemy.orm.exc import NoResultFound
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NoneOf, ValidationError

from models import Category, Item, User, db, OAuth, categories_schema

app = Flask(__name__)
# Load config from config.py file
app.config.from_object('config')
# Allow unnecessary backslash
app.url_map.strict_slashes = False
# Initialize database
db.init_app(app)
# Initialize login system
login_manager = LoginManager()
login_manager.init_app(app)
# Force CSRF for forms
csrf = CSRFProtect()
# Create blueprint for Google
google_bp = make_google_blueprint(
    scope=["profile", "email"]
)
# Register the Google login to /login url
app.register_blueprint(google_bp, url_prefix="/login")
# Set Google login to use SQLAlchemy as database
google_bp.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)


class ItemForm(FlaskForm):
    """
    A form for the Item model. It contains all the fields needed for creating a
    item.
    """
    name = StringField('Name',
                       validators=[DataRequired("Please provide a name."),
                                   NoneOf(['create', 'delete', 'edit'])])
    description = TextAreaField('Description', validators=[
        DataRequired("Please provide a description")])
    submit = SubmitField("Save")

    def validate_name(self, field):
        """
        Checks to see if the name field does not already exist in the database
        for the Item model.
        :param field: The name field, defined by the name of the function
        """
        if Item.query.filter(Item.name == field.data).scalar() is not None:
            raise ValidationError('Name has to be unique.')


class CategoryForm(FlaskForm):
    """
    A form for the Category model. It contains all the fields needed for
    creating a category.
    """
    name = StringField('Name',
                       validators=[DataRequired("Please provide a name."),
                                   NoneOf(['create', 'delete', 'edit'])])
    submit = SubmitField("Add")

    def validate_name(self, field):
        """
        Checks to see if the name field does not already exist in the database
        for the Category model.
        :param field: The name field, defined by the name of the function
        """
        if Category.query.filter(
                Category.name == field.data).scalar() is not None:
            raise ValidationError('Name has to be unique.')


@app.route('/')
def index():
    """
    Generate the index page.
    """
    return render_template('home.html',
                           categories=Category.query.all(),
                           categoryForm=CategoryForm(request.form),
                           latest_items=Item.query.order_by(
                               Item.created_at.desc()),
                           )


@app.route("/logout")
@login_required
def logout():
    """
    Log the user out if already logged in and redirect to index page.
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/categories/<string:category>')
def get_category(category):
    """
    Generate a page with all items for the specific category.
    :param category: name of the category which to render page by
    """
    category = Category.query.filter(Category.name == category).first_or_404()
    return render_template('category.html',
                           categories=Category.query.all(),
                           category=category,
                           items=Item.query.filter(
                               Item.category_id == category.id),
                           categoryForm=CategoryForm(request.form)
                           )


@app.route('/categories/<string:category>/<string:item>')
def get_item(category, item):
    """
    Generate a page for a specific item.
    :param category: name of the category which to render page by
    :param item: name of the item which to render page by
    """
    item = Item.query.join(Item.category).filter(Item.name == item)\
        .filter(Category.name == category).first_or_404()

    return render_template('items/item.html',
                           category=category,
                           item=item
                           )


@app.route('/categories/create', methods=['POST'])
@login_required
def create_category():
    """
    Create a category and redirect to the url where the request came from.
    """
    form = CategoryForm(request.form)

    # Validate the form create the category if form is valid.
    if form.validate():
        category = Category()
        form.populate_obj(category)
        db.session.add(category)
        db.session.commit()

    return redirect(request.referrer)


@app.route('/categories/<string:category>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category):
    """
    Delete the category if a post request else return a page with a
    confirmation for deleting the category. Requires to be logged in.
    :param category: name of the category which to render page by
    """
    category = Category.query.filter(Category.name == category).first_or_404()

    # Delete the category if post request.
    if request.method == 'POST':
        db.session.delete(category)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('categories/delete.html',
                           category=category
                           )


@app.route('/categories/<string:category>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category):
    """
    Generate a page for editing the category.
    Edit the category according to the form if post request.
    :param category: name of the category which to render page by
    """
    category = Category.query.filter(Category.name == category).first_or_404()
    form = CategoryForm(request.form, obj=category)

    # Validate the form and update the category if POST request.
    if request.method == 'POST' and form.validate():
        form.populate_obj(category)
        db.session.commit()
        return redirect(url_for('get_category', category=category.name))

    return render_template('categories/edit.html',
                           category=category,
                           form=form
                           )


@app.route('/categories/<string:category>/create', methods=['GET', 'POST'])
@login_required
def create_item(category):
    """
    Generate a page for creating the item for the category.
    Create the item according to the form if POST request.
    :param category: name of the category which to render page by
    """
    category = Category.query.filter(Category.name == category).first_or_404()
    form = ItemForm(request.form)

    # Validate the form and create the item if POST request.
    if request.method == 'POST' and form.validate():
        item = Item(category=category)
        form.populate_obj(item)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('get_item',
                                category=category.name,
                                item=item.name))

    return render_template('items/create.html',
                           category=category.name,
                           form=form
                           )


@app.route('/categories/<string:category>/<string:item>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_item(category, item):
    """
    Generate a page for editing the item.
    Edit the item according to the form if post request.
    :param category: name of the category which to render page by
    :param item: name of the item which to render page by
    """
    item = Item.query.join(Item.category).filter(Item.name == item)\
        .filter(Category.name == category).first_or_404()
    form = ItemForm(request.form, obj=item)

    # Validate the form and update the item if POST request.
    if request.method == 'POST' and form.validate():
        item.name = form.name.data
        item.description = form.description.data
        db.session.commit()
        return redirect(url_for('edit_item',
                                category=category,
                                item=item.name,
                                form=form))

    return render_template('items/edit.html',
                           category=category,
                           item=item,
                           form=form
                           )


@app.route('/categories/<string:category>/<string:item>/delete',
           methods=['GET', 'POST'])
@login_required
def delete_item(category, item):
    """
    Delete the item if a post request else return a page with a
    confirmation for deleting the item. Requires to be logged in.
    :param category: name of the category which to render page by
    :param item: name of the item which to render page by
    """
    item = Item.query.join(Item.category).filter(Item.name == item)\
        .filter(Category.name == category).first_or_404()

    # Delete the item if post request.
    if request.method == 'POST':
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('items/delete.html',
                           category=category,
                           item=item
                           )


@app.route('/items.json')
def api_items():
    """
    This endpoint returns all items in their categories as JSON.

    :return: json of all items.
    """
    # Returns all categories and when transforming to JSON also return all
    # items for the category.
    g = Category.query.all()
    return categories_schema.jsonify(g)


@login_manager.user_loader
def load_user(id):
    """
    Load the user from the given id.
    :param id: the Id of the user
    :return: User matching the id
    """
    return User.query.get(int(id))


@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    """
    Handle the callback from Google and create a user and log the user in if
    the user does not exist, if the user exist then just log in the user
    matching the credentials.
    """
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
            email=google_info["email"],
            name=google_info["name"],
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
