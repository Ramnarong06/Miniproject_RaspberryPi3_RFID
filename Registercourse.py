import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mfrc522 import SimpleMFRC522

# Reader สำหรับ RFID
reader = SimpleMFRC522()

# ตัวแปรสำหรับเก็บ student_id
student_id = None

# ฟังก์ชันเชื่อมต่อฐานข้อมูล
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="os123",
        database="attendance_db"
    )

# ฟังก์ชันสำหรับสแกนบัตรและเก็บ student_id
def scan_card():
    global student_id
    try:
        # อ่านข้อมูล RFID
        messagebox.showinfo("สแกนบัตร", "กรุณาสแกนบัตรของคุณ")
        rfid = str(reader.read()[0]).strip()
        print(f"RFID: {rfid}")

        # ตรวจสอบว่า RFID ตรงกับข้อมูลนักเรียน
        db = connect_to_db()
        cursor = db.cursor()
        cursor.execute("SELECT student_id FROM students WHERE rfid = %s", (rfid,))
        result = cursor.fetchone()

        if result:
            student_id = result[0]
            messagebox.showinfo("Success", f"สแกนบัตรสำเร็จ! Student ID: {student_id}")
        else:
            messagebox.showerror("Error", "ไม่พบข้อมูลนักเรียนสำหรับบัตรนี้")

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {err}")
    finally:
        cursor.close()
        db.close()

# ฟังก์ชันลงทะเบียนคอร์ส
def register_course(course_id):
    global student_id
    if student_id is None:
        messagebox.showerror("Error", "กรุณาสแกนบัตรก่อนลงทะเบียนเรียน")
        return

    try:
        db = connect_to_db()
        cursor = db.cursor()

        # เพิ่มข้อมูลการลงทะเบียนเรียน
        cursor.execute("""
            INSERT INTO student_courses (student_id, course_id)
            VALUES (%s, %s)
        """, (student_id, course_id))
        db.commit()

    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {err}")
    finally:
        cursor.close()
        db.close()

# ฟังก์ชันสำหรับลงทะเบียนคอร์สหลายรายการ
def on_register_course():
    global student_id
    if student_id is None:
        messagebox.showerror("Error", "กรุณาสแกนบัตรก่อนลงทะเบียนเรียน")
        return

    selected_indices = course_listbox.curselection()  # ดึงรายการที่ผู้ใช้เลือกทั้งหมด
    if selected_indices:
        selected_courses = [filtered_courses[i] for i in selected_indices]  # ดึงข้อมูลจาก filtered_courses ตาม index
        course_ids = [course[0] for course in selected_courses]  # ดึง course_id ของรายการที่เลือก

        for course_id in course_ids:  # ลงทะเบียนแต่ละคอร์ส
            register_course(course_id)

        messagebox.showinfo("Success", "ลงทะเบียนเรียนสำเร็จสำหรับคอร์สที่เลือก")
    else:
        messagebox.showerror("Error", "กรุณาเลือกคอร์สจากรายการ")

# ฟังก์ชันค้นหา
def search_courses():
    search_text = search_entry.get().strip().lower()
    filtered_courses.clear()

    for course in all_courses:
        course_id, day_of_week, start_time, end_time = course
        if search_text in course_id.lower():
            filtered_courses.append(course)

    update_course_listbox()

# ฟังก์ชันอัปเดต Listbox
def update_course_listbox():
    course_listbox.delete(0, tk.END)
    for course in filtered_courses:
        course_id, day_of_week, start_time, end_time = course
        course_display = f"{course_id} | {day_of_week} | {start_time}-{end_time}"
        course_listbox.insert(tk.END, course_display)

# โหลดคอร์สจากฐานข้อมูล
def load_courses():
    db = connect_to_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT course_id, day_of_week, start_time, end_time FROM course_schedule")
        courses = cursor.fetchall()
        return courses
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {err}")
        return []
    finally:
        cursor.close()
        db.close()

# เริ่มต้น UI
root = tk.Tk()
root.title("ระบบลงทะเบียนเรียน")
root.geometry("500x600")

# UI สำหรับสแกนบัตร
scan_button = tk.Button(root, text="สแกนบัตร", font=("Arial", 12), command=scan_card)
scan_button.pack(pady=10)

# UI สำหรับค้นหาและเลือกคอร์ส
search_label = tk.Label(root, text="ค้นหา:", font=("Arial", 12))
search_label.pack()

search_entry = tk.Entry(root, font=("Arial", 12))
search_entry.pack()

search_button = tk.Button(root, text="ค้นหา", font=("Arial", 12), command=search_courses)
search_button.pack(pady=5)

course_listbox = tk.Listbox(root, font=("Arial", 12), width=50, height=15, selectmode=tk.MULTIPLE)
course_listbox.pack(pady=10)

register_button = tk.Button(root, text="ลงทะเบียนเรียน", font=("Arial", 12), command=on_register_course)
register_button.pack(pady=10)

# โหลดคอร์สทั้งหมด
all_courses = load_courses()
filtered_courses = all_courses.copy()
update_course_listbox()

# เริ่มต้นโปรแกรม
root.mainloop()
