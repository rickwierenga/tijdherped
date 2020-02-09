""" Routes for version 1 of the Tijdherped! api. See README.md for details. """
from flask import Blueprint, jsonify, abort, request

from tijdherped import db
from tijdherped.models import User
from tijdherped.errors import CheckInError, CheckOutError

v1 = Blueprint('v1', __name__, url_prefix='/api/v1')


@v1.route('/student/checkin', methods=['POST'])
def checkin():
    print(request.args)
    id, rfid = request.args.get('id'), request.args.get('rfid')
    if id: student = User.query.filter_by(id=id).first()
    elif rfid: student = User.query.filter_by(rfid=rfid).first()
    else: abort(400)
    if not student: return jsonify({'message': 'student not found'}), 404

    try: 
        student.check_in()
        message = "Checked in!"
    except CheckInError as e: message = e.message

    return jsonify({'message': message})


@v1.route('/student/checkout', methods=['POST'])
def checkout():
    id, rfid = request.args.get('id'), request.args.get('rfid')
    if id: student = User.query.filter_by(id=id).first()
    elif rfid: student = User.query.filter_by(rfid=rfid).first()
    else: abort(400)
    if not student: return jsonify({'message': 'student not found'}), 404

    try: 
        student.check_out()
        message = "Checked out!"
    except CheckOutError as e: message = e.message

    return jsonify({'message': message})
