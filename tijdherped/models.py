""" Models """

import datetime
import time

from flask_login import UserMixin

from tijdherped import db
from tijdherped.errors import CheckInError, CheckOutError


class User(db.Model, UserMixin):
    """ Main user class
    
    `role` determines privilages within Tijdherped!
    Supported roles are
    - "teacher"
    - "student"
    """
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String,  unique=True, nullable=True)
    password   = db.Column(db.String,  unique=False, nullable=True)
    first_name = db.Column(db.String,  unique=False, nullable=False)
    last_name  = db.Column(db.String,  unique=False, nullable=False)
    role       = db.Column(db.String,  unique=False, nullable=False)

    # student related
    rfid          = db.Column(db.String, unique=True, nullable=True) # first 5 characters of rfid md5 hash
    check_in_time = db.Column(db.DateTime,  unique=False, nullable=True)
    group_id      = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    group         = db.relationship('Group', backref=db.backref('students', lazy=True, cascade="all,delete"))
    team_id       = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    team          = db.relationship('Team', backref=db.backref('students', lazy=True))

    def __repr__(self):
        return 'User(first name: {}, last name: {}, rfid: {})'.format(self.first_name, self.last_name, self.rfid)

    @property
    def project(self):
        return self.group.current_project

    def check_in(self):
        """ Check in this student.

        Set `checkin_time` to the current time on self. This method modifies the database.

        Student must not be already checked in. If he is, this method throws a CheckInError.
        """
        if self.check_in_time: raise CheckInError(time=self.check_in_time)
        self.check_in_time = datetime.datetime.utcnow()
        db.session.commit()

    def check_out(self):
        """ Check out this student.

        Student must be checked in before checking out.

        This method clears `check_in_time` on self. It also creates a new Session, and adds
        it to the database.
        """
        if self.check_in_time is None: raise CheckOutError()
        checkout = datetime.datetime.utcnow()
        session = Session(student_id=self.id, checkin=self.check_in_time, checkout=checkout)
        db.session.add(session)
        self.check_in_time = None
        db.session.commit()

    @property
    def current_project(self):
        """ Get the current project this group is working on. Can be None """
        if not self.current_project: return None
        project = Project.query.filter_by(id=self.current_project_id).first()
        return project

    @property
    def worked_duration(self):
        return round(sum([session.duration for session in self.sessions]) / 60, 2)
    
    @property
    def progress(self):
        """ How the student is doing in his current project if it exists.
        
        returns {'progress': percentage, 'sufficient': bootstrap style}
        """
        if not self.project: return None
        done = sum([session.duration for session in self.sessions])
        progress = int(done / self.project.net_duration_minutes * 100)
        sufficient = 'bg-success' if progress >= self.project.progress else 'bg-danger'
        return {'progress': progress, 'sufficient': sufficient}


class Group(db.Model):
    """ A group is a class, or grade """
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(2), unique=True, nullable=False)
    current_project_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return 'Group(name: {})'.format(self.name)

    @property
    def current_project(self):
        current_project = Project.query.filter_by(id=self.current_project_id).first()
        return current_project


class Team(db.Model):
    """ Team is a small group of students that work together.

    All teams must be in a group.

    Students in the same team can be validated together.
    """
    __tablename__ = 'teams'

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(2), unique=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    group    = db.relationship('Group', backref=db.backref('teams', lazy=True))



class Session(db.Model):
    """ A single session. 
    
    Properties:
    `checkin`: the check in time.
    `checkout`: the check out time.

    Computed properties:
    `duration`: the duration of this session in minutes, rounded to an integer.
    `duration_lesson`: the duration of this session measured in lessons.
    `date`: the date on which this session took place.
    `start_time`: formatted start time of this session.
    `end_time`: the formatted end time of this session.
    `week_number`: the number of the week in which this sesseion took place.
    """
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    checkin  = db.Column(db.DateTime, unique=False, nullable=False)
    checkout = db.Column(db.DateTime, unique=False, nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    student = db.relationship('User', backref=db.backref('sessions', lazy=True))

    def __repr__(self):
        return 'Session(week: {}, checkin: {}, checkout: {})'.format(self.week_number, self.start_time, self.end_time)

    @property
    def duration(self):
        """ Duration of this session in minutes. """
        timedelta = (self.checkout - self.checkin)
        return round(timedelta.total_seconds() / 60)

    @property
    def duration_lesson(self, lesson_duration=75):
        """ Duration of this session in lessons. 

        args:
            `lesson_duration`: the duration of one lesson in minutes. defaulted to 75
        """
        return round(self.duration / lesson_duration)

    @property
    def date(self):
        """ Date of check in time. Formatted as 31-01 Monday """
        return self.checkin.strftime('%d-%m %A')
    
    @property
    def start_time(self):
        return self.checkin.strftime('%H:%M:%S')

    @property
    def end_time(self):
        return self.checkout.strftime('%H:%M:%S')

    @property
    def week_number(self):
        return self.checkin.isocalendar()[1]    


class Project(db.Model):
    """ A project over which the student's sessions are evaluated. Each project has a 
    duration and a number of weeks the student can be absent. 

    Projects start and end in a certain week. That week is specified by its number. Only
    sessions within the range of weeks are evaluated.
    """
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)
    start_week = db.Column(db.Integer, unique=False, nullable=False)
    end_week = db.Column(db.Integer, unique=False, nullable=False)
    excluded = db.Column(db.Integer, unique=False, nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    group = db.relationship('Group', backref=db.backref('archived_projects', lazy=True))

    @property
    def duration(self):
        return self.end_week - self.start_week

    @property
    def net_duration(self):
        return self.duration - self.excluded

    @property
    def net_duration_minutes(self, lesson_duration=75):
        return (self.duration - self.excluded) * (lesson_duration - 5)

    @property
    def progress(self):
        """ Relative progress of this project on scale 0-100"""
        current_week_number = datetime.datetime.utcnow().isocalendar()[1]
        return round((current_week_number - self.start_week) / self.duration * 100)

    @property
    def progress_minutes(self, lesson_duration=75):
        """ progress in minutes. lesson_duration - 5 because you aren't mean """
        return self.progress * (lesson_duration - 5)  / self.net_duration_minutes

    def __repr__(self):
        return 'Project(name: {})'.format(self.name)