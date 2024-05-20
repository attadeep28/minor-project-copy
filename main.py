import random
from bson import Binary
import secrets
from flask_bcrypt import Bcrypt
import pandas as pd
from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
# Configure MongoDB connection
app.config['BCRYPT_LOG_ROUNDS'] = 10
app.config["MONGO_URI"] = "mongodb://localhost:27017/Scholarlytics"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['email']
        self.user_data = user_data


@login_manager.user_loader
def load_user(email):
    user_data = mongo.db.students.find_one({'email': email})
    if user_data:
        return User(user_data)
    return None


class CourseObject:
    def __init__(self, title, url, is_paid, course_by, skills, cluster_predicted):
        self.image_url = None
        self.title = title
        self.url = url
        self.is_paid = is_paid
        self.course_by = course_by
        self.skills = skills
        self.cluster_predicted = cluster_predicted


class JobObject:
    def __init__(self, advertiser_url, company, employment_type_job_status, job_description, skills, cluster_predicted):
        self.advertiser_url = advertiser_url
        self.company = company
        self.employment_type_job_status = employment_type_job_status
        self.job_description = job_description
        self.skills = skills
        self.cluster_predicted = cluster_predicted


class Student:
    def __init__(self, data):
        self.fullname = data.get('fullname')
        self.email = data.get('email')
        self.phone = data.get('phone')
        self.password = data.get('password')


image_urls = {
    "artificial intelligence": "https://cdn.sanity.io/images/tlr8oxjg/production/9a86b0e680636159ffeae3cb3c8533fb8530a16c-1456x816.png?w=3840&q=80&fit=clip&auto=format",
    "machine learning": "https://cdn.sanity.io/images/tlr8oxjg/production/3565e89270c2601dd194f894bfdbe489f265917e-1456x816.png?w=3840&q=80&fit=clip&auto=format",
    "data science": "https://cdn.sanity.io/images/tlr8oxjg/production/9a9f4a2035426b1f22ab20b7a36a5ffa26c5bc22-1456x816.png?w=3840&q=80&fit=clip&auto=format",
    "network security": "https://cdn.sanity.io/images/tlr8oxjg/production/bdb77d61d1ef7dc459bf17ae010658476c00d420-1456x816.png?w=3840&q=80&fit=clip&auto=format",
    "Android": "https://cdn.sanity.io/images/tlr8oxjg/production/6570b5c208c0588952cf7856467b6b9872a3504a-1456x816.png?w=3840&q=80&fit=clip&auto=format",
    "iOS": "https://cdn.sanity.io/images/tlr8oxjg/production/e91a4659d80f9de0294d1fc4d9c78b23a4e93146-1456x816.png?w=3840&q=80&fit=clip&auto=format",
    "cloud computing": "https://cdn.sanity.io/images/tlr8oxjg/production/054f83d78498f35ed2598bb7a87baf8695bcf4b2-1456x816.png?w=3840&q=80&fit=clip&auto=format"
}


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
        self.skills = data.get('skills', [])
        self.certificates = data.get('certificates', [])
        self.projects = data.get('projects', [])
        # self.studID = data.get('studID')


# Function to insert student Login Details in database
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


# Function to insert student information in the database
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


# Function to update student information in the database
def update_student_info(student_info):
    try:
        # Use the email as a unique identifier
        email = student_info['email']

        # Update the existing student record in the database based on the email
        result = mongo.db.studentsInfo.update_one(
            {'email': email},
            {'$set': student_info}
        )

        # Check if the update was successful
        return result.modified_count > 0

    except Exception as e:
        print(f"Error updating student info: {e}")
        return False


# function which returns the course recommendation for the given profile
def get_course_recommendation(email):
    courses_data = pd.read_csv(r'D:\pythonProject\coursesData.csv')
    item_details = mongo.db.studentsInfo.find_one({'email': email})
    course_obj_container = list()
    uniq_list = []
    for i in item_details['domains']:
        cluster_no_list = courses_data[courses_data['skills'] == i].cluster_predicted.tolist()
        cluster_no_list = list(set(cluster_no_list))
        for j in cluster_no_list:
            course_obj = courses_data[courses_data['cluster_predicted'] == j]
            course_obj_container.append(course_obj)

    recommended = []
    for i in range(len(course_obj_container)):
        # Drop duplicates based on 'title' and 'url'
        data = course_obj_container[i].drop_duplicates(subset=['title', 'url'])
        data = data.values.tolist()
        recommended.append(data)

    # ------------------------
    courses = []
    for course in recommended:
        for c in course:
            courses.append(c)

    list_of_objects = [CourseObject(*sublist) for sublist in courses]
    list_of_objects = sorted(list_of_objects, key=lambda x: x.title)

    for c in list_of_objects:
        s = c.skills
        c.image_url = image_urls.get(s.lower(), random.choice(list(image_urls.values())))

    uniq = set()

    for c in list_of_objects:
        if c.title in uniq:
            continue
        else:
            uniq.add(c.title)
            uniq_list.append(c)

    return uniq_list


# function which returns the course recommendation for the given profile
def get_job_recommendation(email):
    job_data = pd.read_csv(r'D:\pythonProject\jobData.csv')
    item_details = mongo.db.studentsInfo.find_one({'email': email})
    job_obj_container = list()
    uniq_list = []
    for i in item_details['skills']:
        # java_skills_df = df[df['skills'].str.lower() == 'java']
        print(i)
        cluster_no_list = job_data[job_data['skills'].str.lower() == i.lower()]
        job_obj_container.append(cluster_no_list)

    recommended = []
    for i in range(len(job_obj_container)):
        # Drop duplicates based on 'title' and 'url'
        data = job_obj_container[i].drop_duplicates(subset=['advertiserurl'])
        data = data.values.tolist()
        recommended.append(data)

    jobs = []
    for job in recommended:
        for c in job:
            jobs.append(c)

    list_of_objects = [JobObject(*sublist) for sublist in jobs]

    uniq = set()

    for c in list_of_objects:
        if c.advertiser_url in uniq:
            continue
        else:
            uniq.add(c.advertiser_url)
            uniq_list.append(c)

    return uniq_list


# home page route
@app.route('/')
def home():
    return render_template('homePage.html')


# Route for the profile page
@app.route('/profile/<email>')
@login_required
def load_profile(email):
    # print(email)
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    if user_data:
        return render_template("profile.html", student_info=user_data, email=email)
    return "No user present"


# Route for the courses page
@app.route('/Courses/<email>')
@login_required
def load_course(email):
    uniq_list = get_course_recommendation(email)
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    if user_data:
        return render_template("Courses.html", recomended=uniq_list, email=email, student_info=user_data)
    return "No user present"


# Route for the jon page
@app.route('/Job/<email>')
@login_required
def load_job(email):
    uniq_list = get_job_recommendation(email)
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    if user_data:
        return render_template("Jobs.html", recomended=uniq_list, email=email, student_info=user_data)
    return "No user present"


# Route for the Assessment page

@app.route('/quiz/<topic>')
@login_required
def loadQuiz(topic):  # Error handling and API key management (if applicable)
    return render_template('Quize.html', topic=topic)


@app.route('/Assessment/<email>')
@login_required
def load_assessment(email):

    Alltopics = [
        {
            "name": "Data Science",
            "description": "Data science is an interdisciplinary field that uses scientific methods, processes, algorithms, and systems to extract knowledge and insights from structured and unstructured data.",
            "url": "/quiz/dataScience",
            'color': "red"
        },
        {
            "name": "Machine Learning",
            "description": "Machine learning is the scientific study of algorithms and statistical models that computer systems use to perform a specific task without using explicit instructions, relying on patterns and inference instead.",
            "url": "/quiz/machineLearning",
            'color': 'blue'
        },
        {
            "name": "Artificial Intelligence",
            "description": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals.",
            "url": "/quiz/artificialIntelligence",
            'color': 'green'
        },
        {
            "name": "Android",
            "description": "Android is a mobile operating system based on a modified version of the Linux kernel and other open-source software, designed primarily for touchscreen mobile devices such as smartphones and tablets.",
            "url": "/quiz/android",
            'color': 'yellow'
        },
        {
            "name": "Web Development",
            "description": "Web development is the work involved in developing a website for the Internet or an intranet.",
            "url": "/quiz/webDevelopment",
            'color': 'pink'
        },
        {
            "name": "Cloud Computing",
            "description": "Cloud computing is the on-demand availability of computer system resources, especially data storage (cloud storage) and computing power, without direct active management by the user.",
            "url": "/quiz/cloudComputing",
            'color': 'violet'
        },
        {
            "name": "Network Security",
            "description": "Network security consists of the policies, procedures, and technologies implemented to protect digital assets from unauthorized access, misuse, or damage.",
            "url": "/quiz/networkSecurity",
            'color': 'orange'
        },
        {
            "name": "Blockchain",
            "description": "A blockchain is a decentralized, distributed, and oftentimes public, digital ledger consisting of records called blocks that are used to record transactions across multiple computers.",
            "url": "/quiz/blockchain",
            'color': 'sky'
        }
    ]
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    if user_data:
        topics = []
        for d in user_data['domains']:
            if d == 'artificial intelligence':
                topics.append(Alltopics[2])
            elif d == 'machine learning':
                topics.append(Alltopics[1])
            elif d == 'Data Science':
                topics.append(Alltopics[0])
            elif d == 'Android':
                topics.append(Alltopics[3])
            elif d == 'Web Development':
                topics.append(Alltopics[4])
            elif d == 'Cloud Computing':
                topics.append(Alltopics[5])
            elif d == 'Network Security':
                topics.append(Alltopics[6])
            elif d == 'BlockChain':
                topics.append(Alltopics[7])
        return render_template("Assessment.html", email=email, student_info=user_data, topics=topics)
    return "No user present"


# DashBoard
@app.route('/index/<email>')
@login_required
def load_index(email):
    uniq_list = get_course_recommendation(email)
    user = mongo.db.students.find_one({'email': email})
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    if user_data:
        return render_template("index.html", fullname=user['fullname'], email=user['email'],
                               phone=user['phone'], student_data=user_data, recomended=uniq_list)
    return "No user present"


# Signup Route
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
            return render_template('form.html', sample_student_data=sample_student_data)
        else:
            return "Somthing Went Wrong"

    return render_template('signUp.html')


# Login Route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            user = mongo.db.students.find_one({'email': email})

            if user and bcrypt.check_password_hash(user['password'], password):
                # print("hello")
                user_obj = User(user)
                login_user(user_obj)
                return redirect(url_for('load_index', email=email))
            else:
                return render_template("login.html", error="Credentials not matching")

        except Exception as e:
            print(f"Error: {e}")
            return render_template("login.html", error="An error occurred")
    return render_template('login.html')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Student Information input Route
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
        SSC_Mark_sheet = request.files['SSC_Mark_sheet']
        HSC = data.get('HSC', [''])[0]
        HSC_Mark_sheet = request.files['HSC_Mark_sheet']
        department = data.get('department', [''])[0]
        CGPA = data.get('CGPA', [''])[0]
        domains = data.get('domains')
        skill = data.get('skill')

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

        studentInfo = {
            'fName': fName,
            'lName': lName,
            'gender': gender,
            'DOB': DOB,
            'email': email,
            'phone': phone,
            'address': address,
            'SSC': SSC,
            'SSC_Mark_sheet': Binary(SSC_Mark_sheet.read()),
            'HSC': HSC,
            'HSC_Mark_sheet': Binary(HSC_Mark_sheet.read()),
            'department': department,
            'CGPA': CGPA,
            'domains': domains,
            'skill': skill,
            'certificates': certificates,
            'projects': projects
        }
        if insert_student_info(studentInfo):
            return render_template('login.html')
        else:
            return 'Somthing Went Wrong'


# Student Information update Route
@app.route('/update_profile/<email>', methods=['POST', 'GET'])
@login_required
def update(email):
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
        SSC_Mark_sheet = request.files['SSC_Mark_sheet']
        HSC = data.get('HSC', [''])[0]
        HSC_Mark_sheet = request.files['HSC_Mark_sheet']
        department = data.get('department', [''])[0]
        CGPA = data.get('CGPA', [''])[0]
        domains = data.get('domains')
        skills = data.get('skills')
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

        studentInfo = {
            'fName': fName,
            'lName': lName,
            'gender': gender,
            'DOB': DOB,
            'email': email,
            'phone': phone,
            'address': address,
            'SSC': SSC,
            'SSC_Mark_sheet': Binary(SSC_Mark_sheet.read()),
            'HSC': HSC,
            'HSC_Mark_sheet': Binary(HSC_Mark_sheet.read()),
            'department': department,
            'CGPA': CGPA,
            'domains': domains,
            'skills': skills,
            'certificates': certificates,
            'projects': projects
        }
        if update_student_info(studentInfo):
            return render_template('login.html')
        else:
            return 'Somthing Went Wrong'
    else:
        user_data = mongo.db.studentsInfo.find_one({'email': email})
        return render_template('updateProfile.html', student_info=user_data, email=email)


# Resume Generation Route
@app.route('/resume/<email>', methods=['GET'])
@login_required
def resume(email):
    user_data = mongo.db.studentsInfo.find_one({'email': email})
    return render_template('resume.html', student_info=user_data, email=email)


SSC_MARK_SHEET = 'SSC_MARK_SHEET'
HSC_MARK_SHEET = 'HSC_MARK_SHEET'
TMP_PDF_PATH = 'tmp_SSC_MARK_SHEET.pdf'


def create_and_send_pdf(email, pdf_data, mark_sheet_type):
    file_name = f'{email}-{mark_sheet_type}'

    # Create a temporary file to store the PDF content
    temp_pdf_path = f'tmp_{mark_sheet_type}.pdf'
    with open(temp_pdf_path, 'wb') as temp_pdf:
        temp_pdf.write(pdf_data)

    # Send the file for display
    return send_file(temp_pdf_path, as_attachment=False, download_name=file_name, mimetype='application/pdf')


# View SSC Mark sheet
@app.route('/view-ssc/<email>')
@login_required
def view_ssc(email):
    with mongo.cx as client:
        document = mongo.db.studentsInfo.find_one({'email': email})

        if document and 'SSC_Mark_sheet' in document:
            return create_and_send_pdf(email, document['SSC_Mark_sheet'], SSC_MARK_SHEET)

    return 'File not found', 404


# View HSC Mark sheet
@app.route('/view-hsc/<email>')
@login_required
def view_hsc(email):
    with mongo.cx as client:
        document = mongo.db.studentsInfo.find_one({'email': email})

        if document and 'HSC_Mark_sheet' in document:
            return create_and_send_pdf(email, document['HSC_Mark_sheet'], HSC_MARK_SHEET)

    return 'File not found', 404


if __name__ == "__main__":
    app.run(debug=True, port=8000)
