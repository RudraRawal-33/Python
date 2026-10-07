import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

DB_NAME = "attendance.db"

def db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            division TEXT NOT NULL,
            email TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
            UNIQUE(roll_no, attendance_date),
            FOREIGN KEY(roll_no) REFERENCES students(roll_no)
        )
    """)
    conn.commit()
    conn.close()

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance Management System")
        self.root.geometry("1050x650")
        self.root.minsize(950, 600)
        self.build()

    def build(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        header = ttk.Frame(self.root, padding=(20, 15))
        header.pack(fill="x")
        ttk.Label(header, text="Student Attendance Management System",
                  style="Title.TLabel").pack(side="left")

        stats = ttk.Frame(self.root, padding=(20, 5))
        stats.pack(fill="x")
        self.total_var = tk.StringVar()
        self.present_var = tk.StringVar()
        self.absent_var = tk.StringVar()
        self.rate_var = tk.StringVar()
        for i, (label, var) in enumerate([
            ("Students", self.total_var),
            ("Present Records", self.present_var),
            ("Absent Records", self.absent_var),
            ("Overall Attendance", self.rate_var)
        ]):
            box = ttk.LabelFrame(stats, text=label, padding=15)
            box.grid(row=0, column=i, padx=5, sticky="nsew")
            stats.columnconfigure(i, weight=1)
            ttk.Label(box, textvariable=var, font=("Segoe UI", 16, "bold")).pack()

        actions = ttk.Frame(self.root, padding=20)
        actions.pack(fill="x")
        buttons = [
            ("Add Student", self.add_student),
            ("Mark Attendance", self.mark_attendance),
            ("View Attendance", self.view_attendance),
            ("Student Report", self.student_report),
            ("Search Student", self.search_student),
            ("Delete Student", self.delete_student),
        ]
        for i, (text, cmd) in enumerate(buttons):
            ttk.Button(actions, text=text, style="Action.TButton",
                       command=cmd).grid(row=i//3, column=i%3, padx=8, pady=8, sticky="ew")
        for i in range(3):
            actions.columnconfigure(i, weight=1)

        ttk.Label(self.root, text="Attendance is stored locally using SQLite",
                  font=("Segoe UI", 9)).pack(pady=5)
        self.refresh_stats()

    def refresh_stats(self):
        conn = db()
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        present = conn.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'").fetchone()[0]
        absent = conn.execute("SELECT COUNT(*) FROM attendance WHERE status='Absent'").fetchone()[0]
        total_records = present + absent
        rate = (present / total_records * 100) if total_records else 0
        conn.close()
        self.total_var.set(str(total))
        self.present_var.set(str(present))
        self.absent_var.set(str(absent))
        self.rate_var.set(f"{rate:.1f}%")

    def window(self, title, size="550x450"):
        w = tk.Toplevel(self.root)
        w.title(title)
        w.geometry(size)
        w.transient(self.root)
        w.grab_set()
        return w

    def add_student(self):
        w = self.window("Add Student", "560x430")
        f = ttk.Frame(w, padding=25)
        f.pack(fill="both", expand=True)
        vars_ = [tk.StringVar() for _ in range(5)]
        labels = ["Roll Number", "Student Name", "Class", "Division", "Email"]
        for i, label in enumerate(labels):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky="w", pady=9)
            ttk.Entry(f, textvariable=vars_[i], width=35).grid(row=i, column=1, sticky="ew", pady=9)

        def save():
            vals = [v.get().strip() for v in vars_]
            if not all(vals[:4]):
                messagebox.showwarning("Validation", "Roll number, name, class and division are required.", parent=w)
                return
            conn = db()
            try:
                conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", vals)
                conn.commit()
            except sqlite3.IntegrityError:
                conn.close()
                messagebox.showerror("Error", "A student with this roll number already exists.", parent=w)
                return
            conn.close()
            messagebox.showinfo("Success", "Student added successfully.", parent=w)
            w.destroy()
            self.refresh_stats()

        ttk.Button(f, text="Save Student", style="Action.TButton",
                   command=save).grid(row=5, column=0, columnspan=2, pady=25, sticky="ew")

    def mark_attendance(self):
        w = self.window("Mark Attendance", "520x350")
        f = ttk.Frame(w, padding=25)
        f.pack(fill="both", expand=True)
        roll, d, status = tk.StringVar(), tk.StringVar(value=str(date.today())), tk.StringVar(value="Present")

        ttk.Label(f, text="Roll Number").grid(row=0, column=0, sticky="w", pady=10)
        ttk.Entry(f, textvariable=roll).grid(row=0, column=1, sticky="ew", pady=10)
        ttk.Label(f, text="Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(f, textvariable=d).grid(row=1, column=1, sticky="ew", pady=10)
        ttk.Label(f, text="Status").grid(row=2, column=0, sticky="w", pady=10)
        ttk.Combobox(f, textvariable=status, values=["Present", "Absent"],
                     state="readonly").grid(row=2, column=1, sticky="ew", pady=10)

        def save():
            r = roll.get().strip()
            try:
                date.fromisoformat(d.get().strip())
            except ValueError:
                messagebox.showerror("Validation", "Enter a valid date as YYYY-MM-DD.", parent=w)
                return
            conn = db()
            student = conn.execute("SELECT name FROM students WHERE roll_no=?", (r,)).fetchone()
            if not student:
                conn.close()
                messagebox.showerror("Error", "Student roll number not found.", parent=w)
                return
            try:
                conn.execute("INSERT INTO attendance (roll_no, attendance_date, status) VALUES (?, ?, ?)",
                             (r, d.get().strip(), status.get()))
                conn.commit()
            except sqlite3.IntegrityError:
                conn.close()
                messagebox.showerror("Error", "Attendance is already marked for this student on this date.", parent=w)
                return
            conn.close()
            messagebox.showinfo("Success", f"Attendance marked for {student[0]}.", parent=w)
            w.destroy()
            self.refresh_stats()

        ttk.Button(f, text="Mark Attendance", style="Action.TButton",
                   command=save).grid(row=3, column=0, columnspan=2, pady=25, sticky="ew")

    def make_table(self, w, cols, widths):
        frame = ttk.Frame(w, padding=12)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c, width in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=width, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def view_attendance(self):
        w = self.window("Attendance Records", "900x520")
        tree = self.make_table(w, ("ID","Roll No","Name","Date","Status"),
                               [60,100,220,160,120])
        conn = db()
        rows = conn.execute("""
            SELECT a.id, a.roll_no, s.name, a.attendance_date, a.status
            FROM attendance a JOIN students s ON a.roll_no=s.roll_no
            ORDER BY a.attendance_date DESC, a.roll_no
        """).fetchall()
        conn.close()
        for row in rows:
            tree.insert("", "end", values=row)

    def student_report(self):
        w = self.window("Student Attendance Report", "700x430")
        top = ttk.Frame(w, padding=15)
        top.pack(fill="x")
        roll = tk.StringVar()
        ttk.Label(top, text="Roll Number").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=roll, width=25).pack(side="left", padx=5)
        tree = self.make_table(w, ("Roll No","Name","Present","Absent","Total","Attendance %"),
                               [90,180,80,80,80,130])

        def load():
            for item in tree.get_children():
                tree.delete(item)
            conn = db()
            row = conn.execute("""
                SELECT s.roll_no, s.name,
                    SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END),
                    COUNT(a.id)
                FROM students s LEFT JOIN attendance a ON s.roll_no=a.roll_no
                WHERE s.roll_no=?
                GROUP BY s.roll_no, s.name
            """, (roll.get().strip(),)).fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Not Found", "Student not found.", parent=w)
                return
            present, absent, total = row[2] or 0, row[3] or 0, row[4] or 0
            pct = (present/total*100) if total else 0
            tree.insert("", "end", values=(row[0], row[1], present, absent, total, f"{pct:.1f}%"))

        ttk.Button(top, text="Generate", command=load).pack(side="left", padx=5)

    def search_student(self):
        w = self.window("Search Student", "850x450")
        top = ttk.Frame(w, padding=15)
        top.pack(fill="x")
        q = tk.StringVar()
        ttk.Label(top, text="Search name or roll number").pack(side="left", padx=5)
        ttk.Entry(top, textvariable=q, width=30).pack(side="left", padx=5)
        tree = self.make_table(w, ("Roll No","Name","Class","Division","Email"),
                               [100,220,100,100,220])

        def search():
            for item in tree.get_children():
                tree.delete(item)
            term = q.get().strip()
            conn = db()
            rows = conn.execute("""
                SELECT roll_no, name, class_name, division, email FROM students
                WHERE roll_no LIKE ? OR name LIKE ?
                ORDER BY roll_no
            """, (f"%{term}%", f"%{term}%")).fetchall()
            conn.close()
            for row in rows:
                tree.insert("", "end", values=row)

        ttk.Button(top, text="Search", command=search).pack(side="left", padx=5)
        search()

    def delete_student(self):
        w = self.window("Delete Student", "430x250")
        f = ttk.Frame(w, padding=25)
        f.pack(fill="both", expand=True)
        roll = tk.StringVar()
        ttk.Label(f, text="Roll Number").pack(pady=10)
        ttk.Entry(f, textvariable=roll, width=30).pack(pady=5)

        def delete():
            r = roll.get().strip()
            conn = db()
            exists = conn.execute("SELECT name FROM students WHERE roll_no=?", (r,)).fetchone()
            if not exists:
                conn.close()
                messagebox.showerror("Error", "Student not found.", parent=w)
                return
            if not messagebox.askyesno("Confirm", f"Delete {exists[0]} and attendance records?", parent=w):
                conn.close()
                return
            conn.execute("DELETE FROM attendance WHERE roll_no=?", (r,))
            conn.execute("DELETE FROM students WHERE roll_no=?", (r,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Student deleted.", parent=w)
            w.destroy()
            self.refresh_stats()

        ttk.Button(f, text="Delete Student", command=delete).pack(pady=20)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    AttendanceApp(root)
    root.mainloop()
