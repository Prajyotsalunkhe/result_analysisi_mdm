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
    def __init__(self, id, user_id, student_class, roll_no, department, pdf_filename):
        self.id = str(id)
        self.user_id = str(user_id)
        self.student_class = student_class
        self.roll_no = roll_no
        self.department = department
        self.pdf_filename = pdf_filename

    @staticmethod
    def from_dict(source, doc_id):
        return ResultAnalysis(
            id=doc_id,
            user_id=source.get('user_id'),
            student_class=source.get('student_class'),
            roll_no=source.get('roll_no'),
            department=source.get('department'),
            pdf_filename=source.get('pdf_filename')
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'student_class': self.student_class,
            'roll_no': self.roll_no,
            'department': self.department,
            'pdf_filename': self.pdf_filename
        }

class MinorDegreeApplication:
    def __init__(self, id, user_id, prn_no, current_department, preference_1, preference_2, preference_3, preference_4=None):
        self.id = str(id)
        self.user_id = str(user_id)
        self.prn_no = prn_no
        self.current_department = current_department
        self.preference_1 = preference_1
        self.preference_2 = preference_2
        self.preference_3 = preference_3
        self.preference_4 = preference_4

    @staticmethod
    def from_dict(source, doc_id):
        return MinorDegreeApplication(
            id=doc_id,
            user_id=source.get('user_id'),
            prn_no=source.get('prn_no'),
            current_department=source.get('current_department'),
            preference_1=source.get('preference_1'),
            preference_2=source.get('preference_2'),
            preference_3=source.get('preference_3'),
            preference_4=source.get('preference_4')
        )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'prn_no': self.prn_no,
            'current_department': self.current_department,
            'preference_1': self.preference_1,
            'preference_2': self.preference_2,
            'preference_3': self.preference_3,
            'preference_4': self.preference_4
        }
