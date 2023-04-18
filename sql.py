import sqlite3
from sqlite3 import Error


def create_connection(db_file=r"pythonsqlite.db"):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def executeSql(conn, sqlString):
    try:
        c = conn.cursor()
        c.execute(sqlString)
    except Error as e:
        print(e)


def addNewEmployee(conn, employee):
    sql = """ INSERT INTO users(fullname,gender,birthday,cid,phonenumber,shift)
              VALUES(?,?,?,?,?,?) """

    cur = conn.cursor()
    cur.execute(sql, employee)
    conn.commit()

    return cur.lastrowid

def addNewShift(conn, shift):
    sql = """ INSERT INTO shifts(name,timestart,timeend)
              VALUES(?,?,?) """

    cur = conn.cursor()
    cur.execute(sql, shift)
    conn.commit()

    return cur.lastrowid

def removeEmployee(conn, employeeid):
    sql = """ DELETE FROM users
              WHERE id = ? """

    cur = conn.cursor()
    cur.execute(sql, employeeid)
    conn.commit()

    return cur.lastrowid

def getEmployee(employeeid):
    sql = """ SELECT * FROM users WHERE id = ? LIMIT 1 """

    conn = create_connection()
    cur = conn.cursor()
    return cur.execute(sql, (employeeid)).fetchone()

if __name__ == '__main__':
    conn = create_connection(r"pythonsqlite.db")

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        fullname text NOT NULL,
                                        gender integer NOT NULL,
                                        birthday text NOT NULL,
                                        cid text NOT NULL,
                                        phonenumber text NOT NULL,
                                        shift integer NOT NULL,
                                        isactive integer DEFAULT 1 NOT NULL
                                    ); """

    sql_create_shifts_table = """ CREATE TABLE IF NOT EXISTS shifts (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        timestart text NOT NULL,
                                        timeend text NOT NULL
                                    ); """

    sql_create_attendances_table = """ CREATE TABLE IF NOT EXISTS attendances (
                                        id integer PRIMARY KEY,
                                        date text NOT NULL,
                                        userid integer NOT NULL,
                                        shiftid text NOT NULL,
                                        checkintime text,
                                        checkouttime text,
                                        UNIQUE(date, userid, shiftid)
                                    ); """

                                    

    if conn is not None:
        executeSql(conn, sql_create_users_table)
        executeSql(conn, sql_create_shifts_table)
        executeSql(conn, sql_create_attendances_table)

        # addNewEmployee(conn, ('Linh', 0, '2000-09-09', '2000', '0764025361', 1))
        # addNewShift(conn, ('Ca 1', '08:00', '18:00'))
        # addNewShift(conn, ('Ca 2', '12:00', '22:00'))

        # removeEmployee(conn, "1")
        # getEmployee(1)