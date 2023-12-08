import random
from itertools import chain

import numpy as np
from flask import Flask, render_template, request, session
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
import pandas as pd

app = Flask(__name__)

# Configure MongoDB connection
app.config['BCRYPT_LOG_ROUNDS'] = 10
app.config["MONGO_URI"] = "mongodb://localhost:27017/Scholarlytics"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


class MyObject:
    def __init__(self, title, url, is_paid, course_by, skills, cluster_predicted):
        self.image_url = None
        self.title = title
        self.url = url
        self.is_paid = is_paid
        self.course_by = course_by
        self.skills = skills
        self.cluster_predicted = cluster_predicted


class Student:
    def __init__(self, data):
        self.fullname = data.get('fullname')
        self.email = data.get('email')
        self.phone = data.get('phone')
        self.password = data.get('password')


class StudentInfo:
    def __init__(self, data):
        self.fName = data.get('fName')
        self.lName = data.get('lName')
        self.gender = data.get('gender')
        self.DOB = data.get('DOB')
        self.email = data.get('email')
        self.phone = data.get('phone')
        self.address = data.get('address')
        self.SSC = data.get('SSC')
        self.SSC_Mark_sheet = data.get('SSC_Mark_sheet')
        self.HSC = data.get('HSC')
        self.HSC_Mark_sheet = data.get('HSC_Mark_sheet')
        self.department = data.get('department')
        self.CGPA = data.get('CGPA')
        self.domains = data.get('domains', [])
        self.certificates = data.get('certificates', [])
        self.projects = data.get('projects', [])
        # self.studID = data.get('studID')


def insert_student(sample_student_data):
    try:
        new_student = Student(sample_student_data)
        new_student.password = bcrypt.generate_password_hash(new_student.password).decode('utf-8')
        mongo.db.students.insert_one(new_student.__dict__)
        # Check if the insertion was successful by querying for the inserted student
        inserted_student = mongo.db.students.find_one({'email': sample_student_data['email']})
        # Return True only if the student was found (indicating successful insertion)
        return inserted_student is not None
    except Exception as e:
        print(f"Error inserting student: {e}")
        return False


def insert_student_info(student_info):
    try:
        new_student = StudentInfo(student_info)
        mongo.db.studentsInfo.insert_one(new_student.__dict__)
        # Check if the insertion was successful by querying for the inserted student
        inserted_student = mongo.db.students.find_one({'email': student_info['email']})
        # Return True only if the student was found (indicating successful insertion)
        return inserted_student is not None
    except Exception as e:
        print(f"Error inserting student info: {e}")
        return False


def get_course_recom(email):
    courses_data = pd.read_csv(r'D:\pythonProject\coursesData.csv')
    item_details = mongo.db.studentsInfo.find_one({'email': email})

    course_obj_container = list()
    # print(item_details['domains'])

    for i in item_details['domains']:
        cluster_no_list = courses_data[courses_data['skills'] == i].cluster_predicted.tolist()
        cluster_no_list = list(set(cluster_no_list))
        print(cluster_no_list)
        for j in cluster_no_list:
            course_obj = courses_data[courses_data['cluster_predicted'] == j]
            course_obj_container.append(course_obj)

    uniq_course = []
    for i in range(len(course_obj_container)):
        # Drop duplicates based on 'title' and 'url'
        data = course_obj_container[i].drop_duplicates(subset=['title', 'url'])
        data = data.values.tolist()
        print(type(data))
        uniq_course.append(data)
    print(uniq_course)

    return uniq_course


@app.route('/')
def home():
    return render_template('homePage.html')


@app.route('/profile/<email>')
def loadprofile(email):
    print(email)
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    if user_data:
        return render_template("profile.html", student_info=user_data, email=email)
    return "No user present"


@app.route('/index/<email>')
def loadindex(email):
    print(email)
    recomended = get_course_recom(email)
    courses = []
    for course in recomended:
        for c in course:
            courses.append(c)

    list_of_objects = [MyObject(*sublist) for sublist in courses]
    list_of_objects = sorted(list_of_objects, key=lambda x: x.title)
    user = mongo.db.students.find_one({'email': email})
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    image_urls = [
        "https://cdn.sanity.io/images/tlr8oxjg/production/9a86b0e680636159ffeae3cb3c8533fb8530a16c-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "https://cdn.sanity.io/images/tlr8oxjg/production/3565e89270c2601dd194f894bfdbe489f265917e-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "https://cdn.sanity.io/images/tlr8oxjg/production/9a9f4a2035426b1f22ab20b7a36a5ffa26c5bc22-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "https://cdn.sanity.io/images/tlr8oxjg/production/15319392e0b3b29c4301b570e7e83f211b84ca29-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "https://cdn.sanity.io/images/tlr8oxjg/production/ada93729daf922ad0318c8c0295e5cb477921808-1456x816.png?w=3840&q=80&fit=clip&auto=format"
    ]
    my_dict = {
        "artificial intelligence": "https://cdn.sanity.io/images/tlr8oxjg/production/9a86b0e680636159ffeae3cb3c8533fb8530a16c-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "machine learning": "https://cdn.sanity.io/images/tlr8oxjg/production/3565e89270c2601dd194f894bfdbe489f265917e-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "data science": "https://cdn.sanity.io/images/tlr8oxjg/production/9a9f4a2035426b1f22ab20b7a36a5ffa26c5bc22-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "network secuity": "https://cdn.sanity.io/images/tlr8oxjg/production/bdb77d61d1ef7dc459bf17ae010658476c00d420-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "Android": "https://cdn.sanity.io/images/tlr8oxjg/production/6570b5c208c0588952cf7856467b6b9872a3504a-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "iOS": "https://cdn.sanity.io/images/tlr8oxjg/production/e91a4659d80f9de0294d1fc4d9c78b23a4e93146-1456x816.png?w=3840&q=80&fit=clip&auto=format",
        "cloud computing" : "https://cdn.sanity.io/images/tlr8oxjg/production/054f83d78498f35ed2598bb7a87baf8695bcf4b2-1456x816.png?w=3840&q=80&fit=clip&auto=format"
    }

    for c in list_of_objects:
        s = c.skills
        c.image_url = my_dict.get(s.lower(), random.choice(image_urls))

    uniq = set()
    uniq_list = []

    # Now 'image_urls' is a Python list containing the specified URLs.

    for c in list_of_objects:
        if c.title in uniq:
            continue
        else:
            uniq.add(c.title)
            uniq_list.append(c)

    if user_data:
        return render_template("index.html", fullname=user['fullname'], email=user['email'],
                               phone=user['phone'], student_data=user_data, recomended=uniq_list)
    return "No user present"


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            user = mongo.db.students.find_one({'email': email})
            user_data = mongo.db.studentsInfo.find_one({'email': email})

            if user and bcrypt.check_password_hash(user['password'], password):
                courses = []
                recomended = get_course_recom(email)
                for course in recomended:
                    for c in course:
                        courses.append(c)

                list_of_objects = [MyObject(*sublist) for sublist in courses]
                list_of_objects = sorted(list_of_objects, key=lambda x: x.title)
                image_urls = [
                    "https://cdn.sanity.io/images/tlr8oxjg/production/9a86b0e680636159ffeae3cb3c8533fb8530a16c-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "https://cdn.sanity.io/images/tlr8oxjg/production/3565e89270c2601dd194f894bfdbe489f265917e-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "https://cdn.sanity.io/images/tlr8oxjg/production/9a9f4a2035426b1f22ab20b7a36a5ffa26c5bc22-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "https://cdn.sanity.io/images/tlr8oxjg/production/15319392e0b3b29c4301b570e7e83f211b84ca29-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "https://cdn.sanity.io/images/tlr8oxjg/production/ada93729daf922ad0318c8c0295e5cb477921808-1456x816.png?w=3840&q=80&fit=clip&auto=format"
                ]
                my_dict = {
                    "artificial intelligence": "https://cdn.sanity.io/images/tlr8oxjg/production/9a86b0e680636159ffeae3cb3c8533fb8530a16c-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "machine learning": "https://cdn.sanity.io/images/tlr8oxjg/production/3565e89270c2601dd194f894bfdbe489f265917e-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "data science": "https://cdn.sanity.io/images/tlr8oxjg/production/9a9f4a2035426b1f22ab20b7a36a5ffa26c5bc22-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "network secuity": "https://cdn.sanity.io/images/tlr8oxjg/production/bdb77d61d1ef7dc459bf17ae010658476c00d420-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "Android": "https://cdn.sanity.io/images/tlr8oxjg/production/6570b5c208c0588952cf7856467b6b9872a3504a-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "iOS": "https://cdn.sanity.io/images/tlr8oxjg/production/e91a4659d80f9de0294d1fc4d9c78b23a4e93146-1456x816.png?w=3840&q=80&fit=clip&auto=format",
                    "cloud computing": "https://cdn.sanity.io/images/tlr8oxjg/production/054f83d78498f35ed2598bb7a87baf8695bcf4b2-1456x816.png?w=3840&q=80&fit=clip&auto=format"
                }

                for c in list_of_objects:
                    s = c.skills
                    c.image_url = my_dict.get(s.lower(), random.choice(image_urls))

                uniq = set()
                uniq_list = []

                # Now 'image_urls' is a Python list containing the specified URLs.

                for c in list_of_objects:
                    if c.title in uniq:
                        continue
                    else:
                        uniq.add(c.title)
                        uniq_list.append(c)
                return render_template("index.html", fullname=user['fullname'], email=user['email'],
                                       phone=user['phone'], student_data=user_data, recomended=uniq_list)
            else:
                return render_template("login.html", error="Credentials not matching")

        except Exception as e:
            print(f"Error: {e}")
            return render_template("login.html", error="An error occurred")
    return render_template('login.html')


@app.route('/signUp', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        sample_student_data = {
            'fullname': data['fullName'],
            'email': data['email'],
            'phone': data['phone'],
            'password': data['password'],
        }
        if insert_student(sample_student_data):
            return render_template('form.html')
        return "Somthing Went Wrong"

    return render_template('signUp.html')


@app.route('/form', methods=['POST'])
def create():
    if request.method == 'POST':
        data = request.form.to_dict(flat=False)
        # Access data fields
        fName = data.get('fName', [''])[0]
        lName = data.get('lName', [''])[0]
        gender = data.get('gender', [''])[0]
        DOB = data.get('DOB', [''])[0]
        email = data.get('email', [''])[0]
        phone = data.get('phone', [''])[0]
        address = data.get('address', [''])[0]
        SSC = data.get('SSC', [''])[0]
        SSC_Mark_sheet = data.get('SSC_Mark_sheet', [''])[0]
        HSC = data.get('HSC', [''])[0]
        HSC_Mark_sheet = data.get('HSC_Mark_sheet', [''])[0]
        department = data.get('department', [''])[0]
        CGPA = data.get('CGPA', [''])[0]
        domains = data.get('domains')

        # Access certificate data
        certificates = []
        for i in range(len(data.get('InstituteORCompany', []))):
            certificate_data = {
                'InstituteORCompany': data.get('InstituteORCompany', [''])[i],
                'Date_Of_Certification': data.get('Date_Of_Certification', [''])[i],
                'Certificate_Specialization': data.get('Certificate_Specialization', [''])[i],
                'Certificate_Key_Skill': data.get('Certificate_Key_Skill', [''])[i],
            }
            certificates.append(certificate_data)

        # Access project data
        projects = []
        for i in range(len(data.get('projectName', []))):
            project_data = {
                'projectName': data.get('projectName', [''])[i],
                'domain': data.get('domain', [''])[i],
                'duration': data.get('duration', [''])[i],
                'projectDescription': data.get('projectDescription', [''])[i],
            }
            projects.append(project_data)

        # Now you can use these variables as needed
        print(fName, lName, gender, DOB, email, phone, address, SSC, SSC_Mark_sheet, HSC, HSC_Mark_sheet, department,
              CGPA, domains, certificates, projects)

        studentInfo = {
            'fName': fName,
            'lName': lName,
            'gender': gender,
            'DOB': DOB,
            'email': email,
            'phone': phone,
            'address': address,
            'SSC': SSC,
            'SSC_Mark_sheet': SSC_Mark_sheet,
            'HSC': HSC,
            'HSC_Mark_sheet': HSC_Mark_sheet,
            'department': department,
            'CGPA': CGPA,
            'domains': domains,
            'certificates': certificates,
            'projects': projects
        }
        if insert_student_info(studentInfo):
            return render_template('login.html')
        return 'Somthing Went Wrong'


if __name__ == "__main__":
    # get_course_recom('attu@gmail.com')
    app.run(debug=True, port=8000)
