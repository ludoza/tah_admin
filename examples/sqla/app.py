import os
import os.path as op
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

from mqttclient import MQTTClient

from wtforms import validators

import flask_admin as admin
from flask_admin.base import MenuLink
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual

from tah_admin import TahModelView

# Create application
app = Flask(__name__)

# set optional bootswatch theme
# see http://bootswatch.com/3/ for available swatches
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['DEBUG'] = True
# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['DATABASE_FILE'] = 'sample_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
#app.config['SQLALCHEMY_ECHO'] = True


db = SQLAlchemy(app)

app.config['MQTT_SERVER'] = 'planeteer.mooo.com'
app.config['MQTT_PORT'] = 1883

# Create models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    pets = db.relationship('Pet', backref='owner')

    def __str__(self):
        return "{}, {}".format(self.last_name, self.first_name)

    def __repr__(self):
        return "{}: {}".format(self.id, self.__str__())
 
def listens_for(mapper, connection, target, event_type):

    topic = f'{mapper.local_table}'
    payload = f'{event_type[0]} {target.id}'
    app.logger.debug(f'publish {topic}, {payload}')
    MQTTClient.publish(topic, payload=payload) #, qos=1, retain=False)
    MQTTClient.publish_payloads()
    
@db.event.listens_for(User, "after_insert")
def after_insert(mapper, connection, target):
    listens_for(mapper, connection, target, event_type='insert')
    
@db.event.listens_for(User, "after_update")
def after_update(mapper, connection, target):
    listens_for(mapper, connection, target, event_type='update')
    
@db.event.listens_for(User, "after_delete")
def after_delete(mapper, connection, target):
    listens_for(mapper, connection, target, event_type='delete')

app.logger.debug('TEST')
        

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    available = db.Column(db.Boolean)

    def __str__(self):
        return self.name


# Create M2M table
post_tags_table = db.Table('post_tags', db.Model.metadata,
                           db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                           db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                           )


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date)

    user_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    user = db.relationship(User, backref='posts')

    tags = db.relationship('Tag', secondary=post_tags_table)

    def __str__(self):
        return "{}".format(self.title)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))

    def __str__(self):
        return "{}".format(self.name)


class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    key = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(64))

    user_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    user = db.relationship(User, backref='info')

    def __str__(self):
        return "{} - {}".format(self.key, self.value)


class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    parent_id = db.Column(db.Integer, db.ForeignKey('tree.id'))
    parent = db.relationship('Tree', remote_side=[id], backref='children')

    def __str__(self):
        return "{}".format(self.name)


class Screen(db.Model):
    __tablename__ = 'screen'
    id = db.Column(db.Integer, primary_key=True)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)

    @hybrid_property
    def number_of_pixels(self):
        return self.width * self.height


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


# Custom filter class
class FilterLastNameBrown(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if value == '1':
            return query.filter(self.column == "Brown")
        else:
            return query.filter(self.column != "Brown")

    def operation(self):
        return 'is Brown'


# Customized User model admin
inline_form_options = {
    'form_label': "Info item",
    'form_columns': ['id', 'key', 'value'],
    'form_args': None,
    'form_extra_fields': None,
}

class TagAdmin(TahModelView):
    page_size = False
    column_display_pk = True
    column_list = [
        'id',
        'name'
    ]
    column_editable_list = [ 'name']
    def __init__(self, session):
        # Just call parent class with predefined model.
        super(TagAdmin, self).__init__(Tag, session)


        
class UserAdmin(TahModelView):
    column_default_sort = 'id'
    extra_js = [ 
        '//cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.1.0/paho-mqtt.min.js', 
        '//cdnjs.cloudflare.com/ajax/libs/jquery-color/2.1.2/jquery.color.min.js',
        '/static/js/mq.js',
        '/static/js/admin-style.js',]
    extra_css = [ '/static/css/admin-style.css']
    page_size = False
    action_disallowed_list = ['delete', ]
    column_display_pk = True
    column_list = [
        'id',
        'last_name',
        'first_name',
        'email',
        'pets',
    ]
    column_editable_list = [
        #'id',
        'last_name',
        'first_name',
        'email',
        'pets',
    ]
    #column_default_sort = [('last_name', False), ('first_name', False)]  # sort on multiple columns

    # custom filter: each filter in the list is a filter operation (equals, not equals, etc)
    # filters with the same name will appear as operations under the same filter
    column_filters = [
        FilterEqual(column=User.last_name, name='Last Name'),
        FilterLastNameBrown(column=User.last_name, name='Last Name',
                            options=(('1', 'Yes'), ('0', 'No')))
    ]
    inline_models = [(UserInfo, inline_form_options), ]

    # setup create & edit forms so that only 'available' pets can be selected
    def create_form(self):
        return self._use_filtered_parent(
            super(UserAdmin, self).create_form()
        )

    def edit_form(self, obj):
        return self._use_filtered_parent(
            super(UserAdmin, self).edit_form(obj)
        )

    def _use_filtered_parent(self, form):
        form.pets.query_factory = self._get_parent_list
        return form

    def _get_parent_list(self):
        # only show available pets in the form
        return Pet.query.filter_by(available=True).all()



# Customized Post model admin
class PostAdmin(TahModelView):
    column_list = ['id', 'user', 'title', 'date', 'tags']
    column_default_sort = ('date', True)
    column_sortable_list = [
        'id',
        'title',
        'date',
        ('user', ('user.last_name', 'user.first_name')),  # sort on multiple columns
    ]
    column_labels = dict(title='Post Title')  # Rename 'title' column in list view
    column_searchable_list = [
        'title',
        'tags.name',
        'user.first_name',
        'user.last_name',
    ]
    column_labels = {
        'title': 'Title',
        'tags.name': 'tags',
        'user.first_name': 'user\'s first name',
        'user.last_name': 'last name',
    }
    column_filters = [
        'user',
        'title',
        'date',
        'tags',
        filters.FilterLike(Post.title, 'Fixed Title', options=(('test1', 'Test 1'), ('test2', 'Test 2'))),
    ]
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'xls']

    # Pass arguments to WTForms. In this case, change label for text field to
    # be 'Big Text' and add required() validator.
    form_args = dict(
                    text=dict(label='Big Text', validators=[validators.required()])
                )

    form_ajax_refs = {
        'user': {
            'fields': (User.first_name, User.last_name)
        },
        'tags': {
            'fields': (Tag.name,),
            'minimum_input_length': 0,  # show suggestions, even before any user input
            'placeholder': 'Please select',
            'page_size': 5,
        },
    }

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(PostAdmin, self).__init__(Post, session)


class TreeView(TahModelView):
    form_excluded_columns = ['children', ]


class ScreenView(TahModelView):
    column_list = ['id', 'width', 'height', 'number_of_pixels']  # not that 'number_of_pixels' is a hybrid property, not a field
    column_sortable_list = ['id', 'width', 'height', 'number_of_pixels']

    # Flask-admin can automatically detect the relevant filters for hybrid properties.
    column_filters = ('number_of_pixels', )


# Create admin
admin = admin.Admin(app, name='Example: SQLAlchemy', template_mode='bootstrap3')

# Add views
admin.add_view(UserAdmin(User, db.session))
#admin.add_view(TahModelView(Tag, db.session))
admin.add_view(TagAdmin(db.session))

admin.add_view(PostAdmin(db.session))
admin.add_view(TahModelView(Pet, db.session, category="Other"))
admin.add_view(TahModelView(UserInfo, db.session, category="Other"))
admin.add_view(TreeView(Tree, db.session, category="Other"))
admin.add_view(ScreenView(Screen, db.session, category="Other"))
admin.add_sub_category(name="Links", parent_name="Other")
admin.add_link(MenuLink(name='Back Home', url='/', category='Links'))
admin.add_link(MenuLink(name='Google', url='http://www.google.com/', category='Links'))
admin.add_link(MenuLink(name='Mozilla', url='http://mozilla.org/', category='Links'))


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import random
    import datetime

    db.drop_all()
    db.create_all()

    # Create sample Users
    first_names = [
        'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
        'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
        'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
    ]
    last_names = [
        'Brown', 'Brown', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
        'Roberts', 'Khan', 'Clarke', 'Clarke', 'Clarke', 'James', 'Phillips', 'Wilson',
        'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
    ]

    user_list = []
    for i in range(len(first_names)):
        user = User()
        user.first_name = first_names[i]
        user.last_name = last_names[i]
        user.email = first_names[i].lower() + "@example.com"
        user.info.append(UserInfo(key="foo", value="bar"))
        user_list.append(user)
        db.session.add(user)

    # Create sample Tags
    tag_list = []
    for tmp in ["YELLOW", "WHITE", "BLUE", "GREEN", "RED", "BLACK", "BROWN", "PURPLE", "ORANGE"]:
        tag = Tag()
        tag.name = tmp
        tag_list.append(tag)
        db.session.add(tag)

    # Create sample Posts
    sample_text = [
        {
            'title': "de Finibus Bonorum et Malorum - Part I",
            'content': "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor \
                        incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud \
                        exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure \
                        dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \
                        Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt \
                        mollit anim id est laborum."
        },
        {
            'title': "de Finibus Bonorum et Malorum - Part II",
            'content': "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque \
                        laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto \
                        beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur \
                        aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi \
                        nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, \
                        adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam \
                        aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam \
                        corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum \
                        iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum \
                        qui dolorem eum fugiat quo voluptas nulla pariatur?"
        },
        {
            'title': "de Finibus Bonorum et Malorum - Part III",
            'content': "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium \
                        voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati \
                        cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id \
                        est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam \
                        libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod \
                        maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. \
                        Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet \
                        ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur \
                        a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis \
                        doloribus asperiores repellat."
        }
    ]

    for user in user_list:
        entry = random.choice(sample_text)  # select text at random
        post = Post()
        post.user = user
        post.title = entry['title']
        post.text = entry['content']
        tmp = int(1000*random.random())  # random number between 0 and 1000:
        post.date = datetime.datetime.now() - datetime.timedelta(days=tmp)
        post.tags = random.sample(tag_list, 2)  # select a couple of tags at random
        db.session.add(post)

    # Create a sample Tree structure
    trunk = Tree(name="Trunk")
    db.session.add(trunk)
    for i in range(5):
        branch = Tree()
        branch.name = "Branch " + str(i+1)
        branch.parent = trunk
        db.session.add(branch)
        for j in range(5):
            leaf = Tree()
            leaf.name = "Leaf " + str(j+1)
            leaf.parent = branch
            db.session.add(leaf)

    db.session.add(Pet(name='Dog', available=True))
    db.session.add(Pet(name='Fish', available=True))
    db.session.add(Pet(name='Cat', available=True))
    db.session.add(Pet(name='Parrot', available=True))
    db.session.add(Pet(name='Ocelot', available=False))

    db.session.add(Screen(width=500, height=2000))
    db.session.add(Screen(width=550, height=1900))

    db.session.commit()
    return

if __name__ == '__main__':
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

    with app.app_context():
        MQTTClient.create_client()

    # Start app
    app.run(debug=True, port=8080)#, host='0.0.0.0')

