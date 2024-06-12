from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:123456@localhost:3306/lab02"
app.config["SECRET_KEY"] = "dev"
app.config["BOOTSTRAP_BOOTSWATCH_THEME"] = "lux"

app.config['BOOTSTRAP_TABLE_NEW_TITLE'] = '创建'
app.config['BOOTSTRAP_TABLE_DELETE_TITLE'] = '删除'

bootstrap = Bootstrap5(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    from dormitory.models import Manager, Student

    user = Manager.query.get(user_id)
    if user is None:
        user = Student.query.get(user_id)
    return user


login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@app.context_processor
def inject():
    from dormitory.models import Student
    from flask_login import current_user

    if current_user.is_authenticated:
        if isinstance(current_user, Student):
            return dict(user_type="student", name=current_user.name)
        else:
            return dict(user_type="manager", name=current_user.name)
    return dict(user_type="visitor")


from dormitory import views, errors, commands
