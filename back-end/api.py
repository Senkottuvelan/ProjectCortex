import os
import random
import string
from datetime import date, timedelta
from flask import Flask, request
from flask_bcrypt import Bcrypt
from flaskext.mysql import MySQL

app = Flask(__name__, static_url_path="/")
mysql = MySQL(app)
bcrypt = Bcrypt(app)

app.config['MYSQL_DATABASE_HOST'] = os.environ.get("FLASK_DATABASE_HOST")
app.config['MYSQL_DATABASE_USER'] = os.environ.get("FLASK_DATABASE_USER")
app.config['MYSQL_DATABASE_PASSWORD'] = os.environ.get(
    "FLASK_DATABASE_PASSWORD")
app.config['MYSQL_DATABASE_DB'] = "openclou_cortex"


def sql_database(sql_query):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql_query)
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return row


def generate_token():
    letters = string.ascii_letters + string.digits + string.punctuation
    jumble = ''.join(random.choice(letters) for i in range(22))
    sql_query = f"SELECT authtoken FROM openclou_cortex.users WHERE authtoken='{jumble}'"
    authoken = sql_database(sql_query)
    if authoken:
        return generate_token()
    else:
        return jumble


@app.route('/')
def index():
    res = "<h1>Hello world!</h1>"
    return res


@app.after_request
def after_request_func(response):
    response.headers.add("Access-Control-Allow-Origin",
                         "https://crew-grievances.vercel.app")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


@app.route('/api/check', methods=["POST"])
def check_token():
    try:
        _tokenValue = request.json["token"]
        sql_query = f"SELECT expDate FROM openclou_cortex.users WHERE authtoken='{_tokenValue}'"
        exp_date = sql_database(sql_query)
        if exp_date:
            current_date = date.today()
            if exp_date[0] == current_date:
                sql_query = f"UPDATE openclou_cortex.users SET authtoken=NULL, expDate=NULL WHERE authtoken='{_tokenValue}'"
                sql_database(sql_query)
                return {"status": "expired"}
            else:
                sql_query = f"SELECT role FROM openclou_cortex.users WHERE authtoken='{_tokenValue}'"
                role = sql_database(sql_query)
                return {"status": "success", "role": role[0]}
        else:
            return {"status": "false"}
    except Exception as e:
        return {"status": "failure", "reason": e}


@app.route('/api/login', methods=["POST"])
def check_user():
    try:
        _emailValue = request.json["emailValue"]
        _passwordValue = request.json["passwordValue"]

        sql_query = f"SELECT password FROM openclou_cortex.users WHERE email='{_emailValue}'"
        password = sql_database(sql_query)

        if password:
            # pwd = bcrypt.check_password_hash(password[0], _passwordValue)
            if _passwordValue == password[0]:
                exp_date = date.today() + timedelta(days=14)  # yy-mm-dd
                token = generate_token()

                sql_query = f"UPDATE openclou_cortex.users SET authtoken='{token}', expDate='{exp_date}' WHERE email='{_emailValue}'"
                sql_database(sql_query)
                sql_query = f"SELECT role FROM openclou_cortex.users WHERE email='{_emailValue}'"
                role = sql_database(sql_query)

                return {"status": "success", "role": role[0], "token": token}
            else:
                return {"status": "false"}
        else:
            return {"status": "false"}
    except Exception as e:
        return {"status": "failure", "reason": e}


@app.route('/api/submit', methods=["POST"])
def insert_user():
    try:
        _committeeValue = request.json["committeeValue"]
        _projectValue = request.json["projectValue"]
        _grievanceValue = request.json["grievanceValue"]

        sql_query = f"INSERT INTO grievances(committee, project, grievance) VALUES('{_committeeValue}', '{_projectValue}', '{_grievanceValue}')"
        sql_database(sql_query)

        return {"status": "success"}
    except Exception as e:
        return {"status": "failure", "reason": e}


@app.route('/api/view', methods=["POST"])
def grievance_list():
    try:
        _tokenValue = request.json["token"]
        sql_query = f"SELECT role FROM openclou_cortex.users WHERE authtoken='{_tokenValue}'"
        role = sql_database(sql_query)
        if role:
            if role[0] == "admin":
                sql_query = f"SELECT * from openclou_cortex.grievances"
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute(sql_query)
                grievance_list = cursor.fetchall()
                conn.commit()
                cursor.close()
                conn.close()
                return {'status': 'success', "data": grievance_list}
            else:
                return {"status": "false"}
        else:
            return {"status": "false"}
    except Exception as e:
        return {'status': 'failure', "reason": e}


@app.route('/api/logout', methods=["POST"])
def logout():
    try:
        _tokenValue = request.json["token"]
        sql_query = f"UPDATE openclou_cortex.users SET authtoken=NULL, expDate=NULL WHERE authtoken='{_tokenValue}'"
        sql_database(sql_query)
        return {"status": "success"}
    except Exception as e:
        return {"status": "failure", "reason": e}
