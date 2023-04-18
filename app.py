import base64
import datetime
import io
import os
import pickle
import dlib
import face_recognition
import cv2
import sqlite3
from sqlite3 import Error
import numpy as np
from flask import Flask, render_template, redirect, request, send_from_directory
from flask_socketio import SocketIO, emit
from PIL import Image

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

detector = dlib.get_frontal_face_detector()


DB_FILE = r"pythonsqlite.db"

clf = None

with open("trained_knn_model.clf", 'rb') as f:
    clf = pickle.load(f)


def createConnection(db_file=DB_FILE):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = lambda c, r: dict(
            [(col[0], r[idx]) for idx, col in enumerate(c.description)])
        return conn
    except Error as e:
        print(e)

    return conn


def crop_by_bb(img, bb):
    (x, y, w, h) = bb
    return img[y:y+h, x:x+w]


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.jinja')


@socketio.on('checks')
def checks(data_image):
    b = io.BytesIO(base64.b64decode(data_image))
    frame = np.array(Image.open(b))

    small_frame = dlib.resize_image(frame, 0.2)

    faces = face_recognition.face_locations(small_frame)

    if (len(faces) >= 2):
        emit('checks_done', {'status': 1, 'data': 'Có nhiều hơn 1 khuôn mặt'})
        return

    if (len(faces) == 0):
        emit('checks_done', {'status': 1, 'data': 'Không tìm thấy khuôn mặt'})
        return

    face_encoding = face_recognition.face_encodings(small_frame, faces)
    isMatched = clf.kneighbors(face_encoding, n_neighbors=1)[0][0][0] < 0.6

    id = clf.predict(face_encoding)

    if (not isMatched):
        emit('checks_done', {'status': 1, 'data': 'Không nhận diện được'})
        return

    employee = getEmployee(int(id[0]))

    if (employee is None):
        emit('checks_done', {'status': 1, 'data': 'Không nhận diện được'})
        return

    if (employee['isactive'] == 0):
        emit('checks_done', {'status': 1, 'data': 'Đã không còn làm việc'})
        return

    emit('checks_done', {'status': 0, 'data': {
         'id': employee['id'], 'cid': employee['cid'], 'fullname': employee['fullname']}})


@socketio.on('checks_confirm')
def checks_confirm(data):
    status = checkInOut(data['id'], data['type'])
    if (status == 1):
        emit('checks_complete', {'status': 1, 'data': 'Bạn đã checkin rồi'})
        return

    if (status == 2):
        emit('checks_complete', {'status': 1, 'data': 'Bạn đã checkout rồi'})
        return

    if (status == 3):
        emit('checks_complete', {'status': 1, 'data': 'Bạn chưa checkin'})
        return

    emit('checks_complete', {'status': 0})


@app.route('/admin', methods=['GET'])
def adminIndex():
    return redirect('/admin/employees')


@app.route('/admin/employees', methods=['GET'])
def employeeList():
    re = getEmployees()

    return render_template('admin/employee_list.jinja', route='employee', employees=re)


@app.route('/admin/attendances', methods=['GET'])
def schedule():

    return render_template('admin/attendances.jinja', route='attendance')


@app.route('/admin/employees/add', methods=['GET', 'POST'])
def employeeAdd():
    shifts = getShifts()

    formRequest = {
        'shift': 0
    }

    if (request.method == 'GET'):
        return render_template('admin/add_employee.jinja', route='employee', shifts=shifts, formRequest=formRequest)
    else:
        formRequest = request.form.to_dict()
        error = ''
        if (len(formRequest['fullName']) <= 0):
            error
        elif (len(formRequest['birthdayDate']) <= 0):
            error
        elif (len(formRequest['cid']) <= 0):
            error
        elif (len(formRequest['phoneNumber']) <= 0):
            error
        elif (len(formRequest['frames']) <= 0):
            error
        else:
            employeeid = addEmployee((formRequest['fullName'], formRequest['gender'], formRequest['birthdayDate'],
                                      formRequest['cid'], formRequest['phoneNumber'], formRequest['shift'], formRequest['emailAddress']))

            frames = formRequest['frames'].split(";")

            for idx, frame in enumerate(frames):
                filename = f"dataset/{employeeid}/{employeeid}_{idx}.jpeg"
                os.makedirs(os.path.dirname(filename), exist_ok=True)

                b = io.BytesIO(base64.b64decode(frame))
                img = np.array(Image.open(b))
                Image.fromarray(img).save(filename)

            return redirect('/admin/employees')

        return render_template('admin/add_employee.jinja', route='employee', shifts=shifts, formRequest=formRequest)


@app.route('/admin/employees/<employeeid>', methods=['GET', 'POST'])
def employeeEdit(employeeid):
    shifts = getShifts()
    employee = getEmployee(employeeid)
    print(employee)
    formRequest = {
        'fullName': employee['fullname'],
        'birthdayDate': employee['birthday'],
        'cid': employee['cid'],
        'gender': employee['gender'],
        'phoneNumber': employee['phonenumber'],
        'isactive': employee['isactive'],
        'emailAddress': employee['email'],
        'shift': 0,
        'status': employee['isactive'],
    }

    if (request.method == 'GET'):
        return render_template('admin/edit_employee.jinja', route='employee', shifts=shifts, formRequest=formRequest)
    else:
        formRequest = request.form.to_dict()
        error = ''
        if (len(formRequest['fullName']) <= 0):
            error
        elif (len(formRequest['birthdayDate']) <= 0):
            error
        elif (len(formRequest['cid']) <= 0):
            error
        elif (len(formRequest['phoneNumber']) <= 0):
            error
        else:
            employeeid = updateEmployee((formRequest['fullName'], formRequest['gender'], formRequest['birthdayDate'],
                                         formRequest['cid'], formRequest['phoneNumber'], formRequest['shift'], formRequest['emailAddress'], formRequest['status'], employeeid))

            if (len(formRequest['frames']) > 0):
                frames = formRequest['frames'].split(";")

                for idx, frame in enumerate(frames):
                    filename = f"dataset/{employeeid}/{employeeid}_{idx}.jpeg"
                    os.makedirs(os.path.dirname(filename), exist_ok=True)

                    b = io.BytesIO(base64.b64decode(frame))
                    img = np.array(Image.open(b))
                    Image.fromarray(img).save(filename)

            return redirect('/admin/employees')

        return render_template('admin/edit_employee.jinja', route='employee', shifts=shifts, formRequest=formRequest)


@app.route('/admin/employees/<employeeid>/get', methods=['GET'])
def employeeDetail(employeeid):
    shifts = getShifts()
    employee = getEmployee(employeeid)
    print(employee)
    formRequest = {
        'fullName': employee['fullname'],
        'birthdayDate': employee['birthday'],
        'cid': employee['cid'],
        'gender': employee['gender'],
        'phoneNumber': employee['phonenumber'],
        'isactive': employee['isactive'],
        'emailAddress': employee['email'],
        'shift': 0
    }

    return render_template('admin/employee_detail.jinja', shifts=shifts, formRequest=formRequest)


@socketio.on('check_face')
def addDataset(data):
    b = io.BytesIO(base64.b64decode(data['img']))
    frame = np.array(Image.open(b))
    small_frame = dlib.resize_image(frame, 0.2)
    faces = face_recognition.face_locations(small_frame)

    if len(faces) <= 0:
        emit('check_done', '1')
    elif len(faces) > 2:
        emit('check_done', '2')
    else:
        emit('check_done', '3')


@socketio.on('get_attendances')
def getAttendancesList(date):
    attendances = getAttendances(date)
    employees = getActiveEmployees()

    [employee.pop(remove, None) for employee in employees for remove in [
        'cid', 'gender', 'birthday', 'isactive']]

    for employee in employees:
        employee['checkintime'] = ""
        employee['checkouttime'] = ""

    for attendance in attendances:
        for employee in employees:

            if employee['id'] == attendance['userid']:
                if (attendance['checkintime']):
                    employee['checkintime'] = attendance['checkintime']
                if (attendance['checkouttime']):
                    employee['checkouttime'] = attendance['checkouttime']

    emit('attendances_list', employees)


def getAttendances(date):
    conn = createConnection()
    cur = conn.cursor()

    sql = """ SELECT * FROM attendances WHERE date = ?"""
    return cur.execute(sql, (date,)).fetchall()


def getShifts():
    sql = """SELECT * FROM shifts"""

    conn = createConnection()
    cur = conn.cursor()
    return cur.execute(sql).fetchall()


def addEmployee(employee):
    sql = """ INSERT INTO users(fullname,gender,birthday,cid,phonenumber,shift,email)
              VALUES(?,?,?,?,?,?,?) """

    conn = createConnection()
    cur = conn.cursor()

    cur.execute(sql, employee)
    conn.commit()

    return cur.lastrowid


def removeEmployee(employeeid):
    sql = """ DELETE FROM users
              WHERE id = ? """

    conn = createConnection()
    cur = conn.cursor()

    cur.execute(sql, (employeeid,))
    conn.commit()

    return cur.fetchone()


def getEmployees():
    sql = """SELECT * FROM users ORDER BY fullname ASC"""
    c = createConnection().cursor()

    return c.execute(sql).fetchall()


def getActiveEmployees():
    sql = """SELECT * FROM users WHERE isactive = 1 ORDER BY fullname ASC"""
    c = createConnection().cursor()

    return c.execute(sql).fetchall()


def getEmployee(employeeid):
    sql = """ SELECT * FROM users WHERE id = ? LIMIT 1 """

    conn = createConnection()
    cur = conn.cursor()
    return cur.execute(sql, (employeeid,)).fetchone()


def updateEmployee(employee):
    sql = """ UPDATE users SET
        fullname = ?,
        gender = ?,
        birthday = ?,
        cid = ?,
        phonenumber = ?,
        shift = ?,
        email = ?,
        isactive = ?
        WHERE id = ? """

    conn = createConnection()
    cur = conn.cursor()
    cur.execute(sql, employee)
    conn.commit()
    return cur.lastrowid


def checkInOut(employeeid, type):
    employee = getEmployee(employeeid)
    date = str(datetime.date.today())
    time = datetime.datetime.now().strftime("%H:%M:%S")

    sql = """ INSERT OR IGNORE INTO attendances(date,userid,shiftid) VALUES(?,?,?) """
    conn = createConnection()
    cur = conn.cursor()

    cur.execute(
        sql, (date, employeeid, employee['shift'],))
    conn.commit()

    sql = """ SELECT * FROM attendances WHERE date = ? AND userid = ? AND shiftid = ? LIMIT 1"""
    attendance = cur.execute(
        sql, (date, employeeid, employee['shift'],)).fetchone()

    if (attendance['checkintime'] is not None and type == 0):
        return 1

    if (attendance['checkouttime'] is not None and type == 1):
        return 2

    if (attendance['checkintime'] is None and type == 1):
        return 3

    sql = f""" UPDATE attendances SET {'checkintime'if type == 0 else 'checkouttime'} = ? WHERE date = ? AND userid = ? AND shiftid = ?"""

    cur.execute(
        sql, (time, date, employeeid, employee['shift'],))
    conn.commit()

    return 0


if __name__ == '__main__':
    socketio.run(app)
