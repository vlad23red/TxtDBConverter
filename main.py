import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import re
import pandas as pd


def parse_format1(content):
    lines = content.split("\n")
    data = []
    date = None

    for line in lines:
        if "Date:" in line:
            date = line.split(":")[1].strip()

        elif "@" in line:
            parts = line.split(":")
            if len(parts) == 2:
                email, email_password = parts
                data.append({"email": email, "email_password": email_password})

        else:
            parts = line.split(":")
            if len(parts) == 2:
                username, password = parts
                data.append({"username": username, "password": password})

    return data, date


def parse_format2(content):
    data = []
    date = None

    google_block_pattern = r"URL: https://accounts\.google\.com/signin/v2/challenge/pwd(.*?)="
    google_blocks = re.findall(google_block_pattern, content, re.DOTALL)

    for block in google_blocks:
        if "Date:" in block:  # Проверьте наличие даты в блоке
            date = re.search(r"Date: (.+)", block).group(1)

        email = re.search(r"Username: (.+@.+\.com)", block)
        password = re.search(r"Password: (\w+)", block)
        if email and password:
            data.append({"email": email.group(1), "email_password": password.group(1)})

    roblox_block_pattern = r"URL: https://www\.roblox\.com/Login(.*?)="
    roblox_blocks = re.findall(roblox_block_pattern, content, re.DOTALL)

    for block in roblox_blocks:
        username = re.search(r"Username: (\w+)", block)
        password = re.search(r"Password: (\w+)", block)
        if username and password:
            data.append({"username": username.group(1), "password": password.group(1)})

    return data, date


def insert_to_db(data, date=None):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    for item in data:
        if "email" in item:
            cursor.execute("SELECT * FROM users WHERE email=? AND email_password=?", (item["email"], item["email_password"]))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (email, email_password, date) VALUES (?, ?, ?)",
                               (item["email"], item["email_password"], date))
        else:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (item["username"], item["password"]))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (username, password, date) VALUES (?, ?, ?)",
                               (item["username"], item["password"], date))

    conn.commit()
    conn.close()


def clear_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")

    conn.commit()
    conn.close()


def export_to_excel():
    conn = sqlite3.connect('data.db')
    df = pd.read_sql_query("SELECT * from users", conn)
    filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel files", "*.xlsx"), ("All Files", "*.*")])
    if filename:
        df.to_excel(filename, index=False, engine='openpyxl')
        messagebox.showinfo("Успех", "Данные были экспортированы в Excel!")
    conn.close()


def main_gui():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, email_password TEXT, date TEXT)''')

    conn.commit()
    conn.close()

    root = tk.Tk()
    root.title("TXT to DB")

    def load_file():
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='cp1251') as f:
                content = f.read()

        if "URL: https://accounts.google.com/signin/v2/challenge/pwd" in content:
            data, date = parse_format2(content)
        else:
            data, date = parse_format1(content)

        insert_to_db(data, date)  # передайте дату в функцию insert_to_db

        messagebox.showinfo("Успех", "Данные загружены в базу данных!")

    btn_load = tk.Button(root, text="Загрузить текстовый файл", command=load_file)
    btn_load.pack(pady=20)

    btn_clear = tk.Button(root, text="Очистить базу данных", command=clear_database)
    btn_clear.pack(pady=20)

    btn_export = tk.Button(root, text="Экспорт базы данных в Excel", command=export_to_excel)
    btn_export.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    main_gui()
