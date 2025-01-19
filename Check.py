import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pytz
import mysql.connector
from datetime import datetime, timedelta
from mfrc522 import SimpleMFRC522

# ตัวแปรที่ใช้สำหรับ Reader
reader = SimpleMFRC522()

# Timezone
bangkok_tz = pytz.timezone('Asia/Bangkok')

# ฟังก์ชันเชื่อมต่อกับฐานข้อมูล
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="os123",
        database="attendance_db"
    )




# ฟังก์ชันเช็คการเข้าเรียนตาม Workflow ใหม่
def check_attendance():
    db = connect_to_db()
    cursor = db.cursor()

    try:
        # อ่านข้อมูล RFID
        rfid = str(reader.read()[0]).strip()
        print(f"RFID: {rfid}")

        # หารหัสนักเรียนในตาราง students
        cursor.execute("SELECT student_id FROM students WHERE rfid = %s", (rfid,))
        student = cursor.fetchone()
        if not student:
            messagebox.showerror("Error", "ไม่พบข้อมูลนักเรียน")
            return
        student_id = student[0]

        # หารหัสวิชาในตาราง student_courses
        cursor.execute("SELECT course_id FROM student_courses WHERE student_id = %s", (student_id,))
        courses = cursor.fetchall()
        if not courses:
            messagebox.showerror("Error", "นักเรียนยังไม่ได้ลงทะเบียนวิชาเรียน")
            return

        now = datetime.now(bangkok_tz)
        valid_schedule_id = None
        course_name = None
        start_time = None
        end_time = None

        # หารหัส schedule_id ที่ตรงกับเวลาปัจจุบัน
        for course in courses:
            course_id = course[0]
            cursor.execute(
                """
                SELECT schedule_id, course_name, start_time, end_time FROM course_schedule
                INNER JOIN courses ON course_schedule.course_id = courses.course_id
                WHERE course_schedule.course_id = %s AND start_time <= %s AND end_time >= %s
                """,
                (course_id, now, now)
            )
            schedule = cursor.fetchone()
            if schedule:
                valid_schedule_id = schedule[0]
                course_name = schedule[1]
                start_time = schedule[2]
                end_time = schedule[3]
                break

        if not valid_schedule_id:
            messagebox.showerror("Error", "ไม่พบวิชาที่มีการเรียนในเวลานี้")
            return

        # แปลง start_time และ end_time
        if isinstance(start_time, timedelta):  # กรณีเป็น timedelta
            start_time = (datetime.min + start_time).time()
        if isinstance(end_time, timedelta):  # กรณีเป็น timedelta
            end_time = (datetime.min + end_time).time()

        # ใช้ datetime.combine และเพิ่ม time zone ให้ start_time และ end_time
        start_time = datetime.combine(now.date(), start_time).replace(tzinfo=bangkok_tz)
        end_time = datetime.combine(now.date(), end_time).replace(tzinfo=bangkok_tz)

        # ตรวจสอบว่ามีการเช็คชื่อใน schedule_id นี้แล้วหรือยัง
        cursor.execute(
            """
            SELECT * FROM attendance WHERE student_id = %s AND schedule_id = %s
            """,
            (student_id, valid_schedule_id)
        )
        existing_attendance = cursor.fetchone()
        if existing_attendance:
            messagebox.showwarning("Warning", "นักเรียนคนนี้ได้เช็คชื่อในวิชานี้ไปแล้ว")
            return

        # ตรวจสอบสถานะการเข้าเรียน
        
        status = "OUT"  # กำหนดสถานะเริ่มต้นเป็น "ขาด"
        if start_time <= now <= start_time + timedelta(minutes=15):
            status = "PASS"
        elif start_time + timedelta(minutes=15) < now <= start_time + timedelta(minutes=30):
            status = "LATE"
        elif start_time + timedelta(minutes=30) < now <= end_time:
            status = "OUT"

        # พิมพ์ค่า status ที่จะถูกส่งไป
        print(f"Status: {status}")

        # เพิ่มข้อมูลลงในตาราง attendance
        cursor.execute(
            """
            INSERT INTO attendance (student_id, schedule_id, timestamp, status)
            VALUES (%s, %s, %s, %s)
            """,
            (student_id, valid_schedule_id, now, status)  # ตรวจสอบให้แน่ใจว่า status เป็นค่าที่ถูกต้อง
        )
        db.commit()

        # แสดงผลใน MessageBox
        messagebox.showinfo(
            "Success",
            (
                f"เช็คชื่อสำเร็จ!\n\n"
                f"Student ID: {student_id}\n"
                f"Course ID: {course_id}\n"
                f"Course Name: {course_name}\n"
                f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Status: {status}"
            )
        )

    except mysql.connector.Error as err:
        print(f"เกิดข้อผิดพลาด: {err}")
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {err}")

    finally:
        cursor.close()
        db.close()


# ฟังก์ชันสำหรับเช็คการเข้าเรียนเมื่อกดปุ่ม
def on_check_attendance():
    check_attendance()

# UI Components
root = tk.Tk()
root.title("ระบบเช็คชื่อ")
root.geometry("400x300")

instruction_label = tk.Label(root, text="โปรดสแกน RFID ของนักเรียน", font=("Arial", 14))
instruction_label.pack(pady=20)

check_button = tk.Button(root, text="เช็คชื่อ", font=("Arial", 12), command=on_check_attendance)
check_button.pack(pady=10)

result_label = tk.Label(root, text="ผลลัพธ์จะปรากฏที่นี่", font=("Arial", 12))
result_label.pack(pady=20)

# เริ่มต้น UI
root.mainloop()
