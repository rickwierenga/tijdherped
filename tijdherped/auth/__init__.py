from tijdherped import login_manager
from tijdherped.models import User

from .routes import auth


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()