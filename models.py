from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = str(id)
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def from_dict(source, doc_id):
        return User(id=doc_id, username=source.get('username'), password_hash=source.get('password_hash'))

    def to_dict(self):
        return {
            'username': self.username,
            'password_hash': self.password_hash
        }

class ResultAnalysis:
    def __init__(self, id, user_id, student_class, roll_no, department, pdf_filename, name=None, subjects=None, summary=None, last_updated=None):
        self.id = str(id)
        self.user_id = str(user_id)
        self.student_class = student_class
        self.roll_no = roll_no
        self.department = department
        self.pdf_filename = pdf_filename
        self.name = name
        self.subjects = subjects or []
        self.summary = summary or {}
        self.last_updated = last_updated

    @staticmethod
    def from_dict(source, doc_id):
        return ResultAnalysis(
            id=doc_id,
            user_id=source.get('user_id'),
            student_class=source.get('student_class'),
            roll_no=source.get('roll_no'),
            department=source.get('department') or source.get('dept'),
            pdf_filename=source.get('pdf_filename'),
            name=source.get('name'),
            subjects=source.get('subjects'),
            summary=source.get('summary'),
            last_updated=source.get('last_updated')
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'student_class': self.student_class,
            'roll_no': self.roll_no,
            'department': self.department,
            'pdf_filename': self.pdf_filename,
            'name': self.name,
            'subjects': self.subjects,
            'summary': self.summary,
            'last_updated': self.last_updated
        }

class MinorDegreeApplication:
    def __init__(self, id, user_id, prn, branch, pref1, pref2, pref3, pref4=None, name='Student', total_marks=0):
        self.id = str(id)
        self.user_id = str(user_id)
        self.prn = prn
        self.branch = branch
        self.pref1 = pref1
        self.pref2 = pref2
        self.pref3 = pref3
        self.pref4 = pref4
        self.name = name
        self.total_marks = total_marks

    @staticmethod
    def from_dict(source, doc_id):
        return MinorDegreeApplication(
            id=doc_id,
            user_id=source.get('user_id'),
            prn=source.get('PRN') or source.get('prn_no'),
            branch=source.get('Branch') or source.get('current_department'),
            pref1=source.get('PREFERENCE 1') or source.get('preference_1'),
            pref2=source.get('PREFERENCE 2') or source.get('preference_2'),
            pref3=source.get('PREFERENCE 3') or source.get('preference_3'),
            pref4=source.get('PREFERENCE 4') or source.get('preference_4'),
            name=source.get('Name', 'Student'),
            total_marks=source.get('Total Marks', 0)
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'PRN': self.prn,
            'Branch': self.branch,
            'PREFERENCE 1': self.pref1,
            'PREFERENCE 2': self.pref2,
            'PREFERENCE 3': self.pref3,
            'PREFERENCE 4': self.pref4,
            'Name': self.name,
            'Total Marks': self.total_marks
        }

