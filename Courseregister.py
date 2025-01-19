import tkinter as tk
from tkinter import messagebox
import mysql.connector
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# ตัวแปรที่ใช้สำหรับ Reader
reader = SimpleMFRC522()

# ตัวแปรสำหรับ Buzzer
BUZZER_PIN = 40

# ตั้งค่า GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# ฟังก์ชันสำหรับเสียงบี๊บ
def play_buzzer_success():
    """เสียงบี๊บเมื่อสำเร็จ"""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    t.sleep(0.1)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def play_buzzer_error():
    """เสียงบี๊บเมื่อเกิดข้อผิดพลาด"""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    t.sleep(0.1)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    t.sleep(0.1)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    t.sleep(0.1)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

# ฟังก์ชันเชื่อมต่อกับฐานข้อมูล
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="os123",
        database="attendance_db"
    )

# ฟังก์ชันลงทะเบียนเรียน
def register_course():
    db = connect_to_db()
    cursor = db.cursor()

    try:
        # กรอก course_id
        course_id = course_entry.get().strip()
        if not course_id:
            play_buzzer_error()
            messagebox.showerror("Error", "กรุณากรอก course_id")
            return

        # ตรวจสอบว่า course_id มีอยู่ในฐานข้อมูลหรือไม่
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        course_result = cursor.fetchone()
        if not course_result:
            play_buzzer_error()
            messagebox.showerror("Error", "ไม่พบข้อมูล course_id นี้")
            return

        # ขอให้ผู้ใช้สแกน Student Card
        play_buzzer_success()
        messagebox.showinfo("Success", "Place your Student Card")

        # อ่านข้อมูล RFID
        rfid = str(reader.read()[0]).strip()
        print(f"RFID: {rfid}")

        # ตรวจสอบว่าเป็น RFID ของนักเรียน
        cursor.execute("SELECT student_id FROM students WHERE rfid = %s", (rfid,))
        result = cursor.fetchone()
        if not result:
            play_buzzer_error()
            messagebox.showerror("Error", "ไม่พบข้อมูลนักเรียน")
            return
        student_id = result[0]

        # เพิ่มข้อมูลลงในตาราง student_courses
        cursor.execute("""
            INSERT INTO student_courses (student_id, course_id)
            VALUES (%s, %s)
        """, (student_id, course_id))
        db.commit()

        play_buzzer_success()
        messagebox.showinfo("Success", "ลงทะเบียนเรียนสำเร็จ")

    except mysql.connector.Error as err:
        print(f"เกิดข้อผิดพลาด: {err}")
        play_buzzer_error()
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {err}")

    finally:
        cursor.close()
        db.close()

# ฟังก์ชันสำหรับลงทะเบียนเมื่อกดปุ่ม
def on_register_course():
    register_course()

# UI Components
root = tk.Tk()
root.title("ระบบลงทะเบียนเรียน")
root.geometry("400x300")

# UI สำหรับกรอก course_id
course_label = tk.Label(root, text="กรอก Course ID:", font=("Arial", 14))
course_label.pack(pady=10)

course_entry = tk.Entry(root, font=("Arial", 12))
course_entry.pack(pady=10)

register_button = tk.Button(root, text="ลงทะเบียนเรียน", font=("Arial", 12), command=on_register_course)
register_button.pack(pady=20)

# เริ่มต้น UI
root.mainloop()

# ปิดการใช้งาน GPIO เมื่อโปรแกรมหยุดทำงาน
GPIO.cleanup()
