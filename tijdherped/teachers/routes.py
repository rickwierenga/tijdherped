import datetime
from functools import wraps
import os
import operator

from flask import Blueprint, redirect, url_for, render_template, flash, abort, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from tijdherped import db, bcrypt, app
from tijdherped.models import Group, User, Team, Project, Session
from tijdherped.errors import CheckInError, CheckOutError

from .forms import *

teachers = Blueprint('teachers', __name__, url_prefix='/teachers/', template_folder='templates/teachers/')


def teachers_only(function):
    """ Block non teachers """
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not hasattr(current_user, 'role'):
            flash('Teachers only!', 'danger')
            return redirect(url_for('auth.login'))
        elif not current_user.role == 'teacher':
            flash('Teachers only!', 'danger')
            return redirect('auth.login')
        return function(*args, **kwargs)
    return wrapper


@teachers.route('/')
@teachers_only
def index():
    groups = Group.query.all()
    groups = sorted(groups, key=operator.attrgetter('name'))
    working = db.session.query(User).filter(User.check_in_time != None).all()

    new_group_form = NewGroup()
    new_student_form = NewStudent()
    new_team_form = NewTeamForm()
    new_project_form = NewProjectForm()

    return render_template('home.html',
        groups=groups,
        working=working,
        new_group_form=new_group_form,
        new_student_form=new_student_form,
        new_team_form=new_team_form,
        new_project_form=new_project_form
    )


@teachers.route('/students/<string:id>')
@teachers_only
def student(id):
    student = User.query.filter_by(id=id).first_or_404()
    groups = Group.query.all()
    rfid_form = UpdateRFIDForm()
    new_session_form = NewSessionForm()
    return render_template('student.html',
        student=student,
        groups=groups,
        rfid_form=rfid_form,
        new_session_form=new_session_form
    )


# TODO: Replace with API.
@teachers.route('/students/<int:id>/rfid/', methods=['POST', 'DELETE'])
@teachers_only
def rfid(id):
    student = User.query.filter_by(id=id).first_or_404()

    if request.method == 'POST':
        form = UpdateRFIDForm()
        if form.validate_on_submit():
            rfid = form.rfid.data
            student.rfid = rfid
            db.session.commit()

            return redirect(url_for('teachers.student', id=student.id))
    elif request.method == 'DELETE':
        student.rfid = None
        db.session.commit()
        return 'OK', 200

    return abort(400)

# TODO: Replace with API.
# TODO: Add cancel.
@teachers.route('/students/<int:id>/checkin/')
@teachers_only
def checkin(id):
    student = User.query.filter_by(id=id).first_or_404()
    try:
        student.check_in()
        flash('{} was checked in.'.format(student.first_name), 'success')
    except CheckInError as e:
        message = e.message
        flash(message, 'danger')
    return redirect(url_for('teachers.student', id=id))


# TODO: Replace with API.
@teachers.route('/students/<int:id>/checkout/')
@teachers_only
def checkout(id):
    student = User.query.filter_by(id=id).first_or_404()
    try:
        student.check_out()
        flash('{} was checked out'.format(student.first_name), 'success')
    except CheckOutError as e:
        message = e.message
        flash(message, 'danger')
    return redirect(url_for('teachers.student', id=id))


@teachers.route('/students/<int:id>/sessions/add', methods=['POST'])
@teachers_only
def add_session(id):
    form = NewSessionForm()
    if form.validate_on_submit():
        student = User.query.filter_by(id=id).first_or_404()
        checkin = datetime.datetime.utcnow()
        checkout = checkin + datetime.timedelta(minutes=form.minutes.data)
        session = Session(checkin=checkin, checkout=checkout, student=student)
        db.session.add(session)
        db.session.commit()
        flash('Session added'.format(student.first_name), 'success')
        return redirect(url_for('teachers.student', id=id))
    return abort(400)


@teachers.route('/students/new', methods=['POST'])
@teachers_only
def new_student():
    form = NewStudent()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        group_id = request.form.get('group_id')
        _ = Group.query.filter_by(id=group_id).first_or_404()
        student = User(first_name=first_name, last_name=last_name, group_id=group_id, role='student')
        db.session.add(student)
        db.session.commit()

        return redirect(url_for('teachers.student', id=student.id))
    return abort(400)


@teachers.route('/groups/new', methods=['POST'])
@teachers_only
def new_group():
    form = NewGroup()
    if form.validate_on_submit():
        name = form.name.data
        group = Group(name=name)
        db.session.add(group)
        db.session.commit()

        """
        if form.excel_file:
            f = form.excel_file.data
            filename = secure_filename(f.filename)
            os.makedirs('/tmp/tijdherped', exist_ok=True)
            p = os.path.join('/tmp/tijdherped', filename)
            f.save(p)
            df = pd.read_excel(p, names=['first', 'last'], header=None)
            print(df.head())
            for _, info in df.iterrows():
                student = User(first_name=info['first'], last_name=info['last'], role='student', group_id=group.id)
                print(student, student.group)
                db.session.add(student)
            os.remove(p)
        """

        db.session.commit()
        return redirect(url_for('teachers.index'))
    return abort(400)


@teachers.route('/teams/new', methods=['GET', 'POST'])
@teachers_only
def new_team():
    form = NewTeamForm()
    if form.validate_on_submit():
        group = Group.query.filter_by(id=request.form.get('group_id')).first_or_404()
        name = form.name.data
        team = Team(name=name, group=group)
        db.session.add(team)
        db.session.commit()
        return redirect(url_for('teachers.index'))
    return abort(400)


@teachers.route('/student/<string:id>/update_group', methods=['POST'])
@teachers_only
def update_group(id):
    group_id = request.form.get('group')
    group = Group.query.filter_by(id=group_id).first()
    student = User.query.filter_by(id=id).first_or_404()
    student.group = group
    db.session.commit()
    flash('Group updated successfully.', 'success')
    return redirect(url_for('teachers.student', id=student.id))


@teachers.route('/student/<string:id>/update_team', methods=['POST'])
@teachers_only
def update_team(id):
    """ Update team for a student """
    team_id = request.form.get('team')
    team = Team.query.filter_by(id=team_id).first()
    student = User.query.filter_by(id=id).first_or_404()
    student.team = team # can be none
    db.session.commit()
    flash('Team updated successfully.', 'success')
    return redirect(url_for('teachers.student', id=student.id))


@teachers.route('/projects/new', methods=['GET', 'POST'])
@teachers_only
def new_project():
    """ Add a new project to the group with `group_id`.

    Set new project to the groups current project. The current project will be archived. 
    """
    form = NewProjectForm()
    if form.validate_on_submit():
        group_id = request.form.get('group_id')
        group = Group.query.filter_by(id=group_id).first_or_404()
        project = Project(
            name=form.name.data,
            start_week=form.start_week.data,
            end_week=form.end_week.data,
            excluded=form.excluded.data,
            group_id=group_id
        )
        db.session.add(project)
        db.session.commit()
        group.current_project_id = project.id
        db.session.commit()
        return redirect(url_for('teachers.index'))
    return abort(400)
