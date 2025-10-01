from pyautogui import printInfo


class Student:
    def __init__(self, student_id, name, age, grade, email=""):
        self.student_id = student_id
        self.name = name
        self.age = age
        self.grade = grade
        self.email = email
        self.courses = []

    def add_course(self, course_name):
        if course_name not in self.courses:
            self.courses.append(course_name)

    def get_info(self):
        return {
            "ID": self.student_id,
            "Name": self.name,
            "Age": self.age,
            "Grade": self.grade,
            "Email": self.email,
            "Courses": ", ".join(self.courses) if self.courses else "No courses"
        }


class StudentManagementSystem:
    def __init__(self):
        self.students = {}

    def add_student(self, student):
        if student.student_id in self.students:
            print(f"Student with ID {student.student_id} already exists!")
            return False
        self.students[student.student_id] = student
        return True

    def remove_student(self, student_id):
        if student_id in self.students:
            del self.students[student_id]
            return True
        return False

    def get_student(self, student_id):
        return self.students.get(student_id)

    def list_all_students(self):
        return [student.get_info() for student in self.students.values()]


# Example usage
if __name__ == "__main__":
    # Create a new student management system
    sms = StudentManagementSystem()

    # Add some sample students
    student1 = Student("S001", "John Doe", 18, "12th", "john.doe@example.com")
    student1.add_course("Mathematics")
    student1.add_course("Physics")

    student2 = Student("S002", "Jane Smith", 17, "11th", "jane.smith@example.com")
    student2.add_course("Biology")
    student2.add_course("Chemistry")

    # Add students to the system
    sms.add_student(student1)
    sms.add_student(student2)
    print(sms)
    print("hiii")
    # Print all students
    print("\nAll Students:")
    print("-" * 50)
    for student_info in sms.list_all_students():
        for key, value in student_info.items():
            print(f"{key}: {value}")
        print("-" * 50)


    all_students = sms.list_all_students()
    if all_students:
        print(all_students[0])
