import time
from tijdherped import db, bcrypt
from tijdherped.models import User, Group

db.create_all()
db.session.rollback()

v5 = Group(name='v5')
db.session.add(v5)
db.session.commit()

password = bcrypt.generate_password_hash('password').decode('utf-8')
rick = User(username='rickwierenga', password=password, \
    first_name='Rick', last_name='Wierenga', group=v5, role='student')
teacher = User(username='teachertest', password=password, \
    first_name='Teacher', last_name='Test', role='teacher')
db.session.add(rick)
db.session.add(teacher)
db.session.commit()
