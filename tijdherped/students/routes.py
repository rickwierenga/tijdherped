from flask import Blueprint, render_template
from flask_login import current_user

from tijdherped.models import User

students = Blueprint('students', __name__, url_prefix='/students/', template_folder='templates/students/')


@students.route('/')
def index():
    id = current_user.id
    student = User.query.filter_by(id=id).first()
    return render_template('student-home.html', student=student)
