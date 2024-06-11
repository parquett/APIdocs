import ply.lex as lex
import ply.yacc as yacc
from customtkinter import *
from openai import OpenAI
import threading
import os
import tkinter as tk
from tkinter import filedialog

tokens = (
    'CREATE',
    'DELETE',
    'GET',
    'RENAME',
    'EXIT',
    'DOC',
    'ADD',
    'FILENAME',
    'STRING',
    'INFO',
    'DIFFICULTY'
)

t_CREATE = r'CREATE'
t_DELETE = r'DELETE'
t_GET = r'GET'
t_DOC = r'DOC'
t_RENAME = r'RENAME'
t_EXIT = r'EXIT'
t_ADD = r'ADD'
t_INFO = r'INFO'
t_DIFFICULTY = r'(easy|medium|hard)'
t_ignore = ' \t'

def t_FILENAME(t):
    r'\#[^\s]+'
    t.value = t.value[1:]  # Remove the '#' prefix
    return t

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]  # Strip off the quotes
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

def p_command(p):
    '''command : create_command
               | delete_command
               | get_command
               | rename_command
               | exit_command
               | add_command
               | info_command
               | doc_command'''
    p[0] = p[1]  # Pass up the result from sub-rules

def p_create_command(p):
    'create_command : CREATE FILENAME'
    p[0] = handle_create(p[2])

def p_delete_command(p):
    'delete_command : DELETE FILENAME'
    p[0] = handle_delete(p[2])

def p_get_command(p):
    'get_command : GET FILENAME'
    p[0] = handle_get(p[2])

def p_rename_command(p):
    'rename_command : RENAME FILENAME FILENAME'
    p[0] = handle_rename(p[2], p[3])

def p_exit_command(p):
    'exit_command : EXIT'
    p[0] = handle_exit()

def p_add_command(p):
    'add_command : ADD FILENAME STRING'
    p[0] = handle_add(p[2], p[3])

def p_info_command(p):
    'info_command : INFO STRING STRING DIFFICULTY'
    p[0] = handle_info(p[2], p[3], p[4])

def p_doc_command(p):
    'doc_command : DOC FILENAME'
    p[0] = handle_doc(p[2])

def p_error(p):
    if p:
        return f"Syntax error at '{p.value}'"
    else:
        return "Syntax error at EOF"

# Command handling functions
def handle_create(filename):
    if os.path.exists(filename):
        return f"Error: File '{filename}' already exists."
    else:
        try:
            with open(filename, 'w') as f:
                f.write("")
            return f"File created: {filename}"
        except IOError as e:
            return f"Error: {e}"

def handle_delete(filename):
    try:
        os.remove(filename)
        return f"File '{filename}' deleted."
    except FileNotFoundError:
        return f"Error: File '{filename}' not found."
    except IOError as e:
        return f"Error deleting file: {e}"

def handle_get(filename):
    try:
        with open(filename, 'r') as f:
            contents = f.read()
        return f"Contents of {filename}:\n{contents}"
    except FileNotFoundError:
        return f"Error: File '{filename}' not found"
    except IOError as e:
        return f"Error: {e}"

def handle_rename(old_filename, new_filename):
    try:
        os.rename(old_filename, new_filename)
        return f"File renamed from {old_filename} to {new_filename}"
    except OSError as e:
        return f"Error renaming file: {e}"

def handle_doc(filename):
    try:
        with open(filename, 'r') as f:
            contents = f.read()
        return contents
    except FileNotFoundError:
        return f"Error: File '{filename}' not found."
    except IOError as e:
        return f"Error reading file: {e}"

def handle_add(filename, text):
    try:
        with open(filename, 'a') as f:
            f.write(text + "\n")
        return f"Text added to {filename}"
    except FileNotFoundError:
        return f"Error: File '{filename}' not found"
    except IOError as e:
        return f"Error: {e}"

def handle_exit():
    print("Exiting DSL...")
    sys.exit(0)

def handle_info(api_name, documentation, difficulty):
    info_str = f"API Name: {api_name}, Documentation: {documentation}, Difficulty: {difficulty}\n"
    try:
        with open("info_records.txt", "a") as file:
            file.write(info_str)
        return f"Info saved: API Name - {api_name}, Difficulty - {difficulty}"
    except IOError as e:
        return f"Error writing info: {e}"

parser = yacc.yacc()

def main():
    s = input('dsl > ')
    result = parser.parse(s)
    if result == None:
        result = "Error"
    print(result)
    print(type(result))

# API Setup
api_key = "###"
client = OpenAI(api_key=api_key)
uploaded_file_content = ""

def get_response_async(content, textbox):
    def thread_target():
        prompt = content
        response = " "
        if prompt.startswith("DOC"):
            # Special handling for DOC command
            prompt = f"write a documentation for this code:\n{prompt}"
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="gpt-3.5-turbo",
                )
                response = chat_completion.choices[0].message.content
            except Exception as e:
                response = str(e)
        elif "#INFO" in prompt:
            response = parser.parse(prompt)
            words_list = prompt.split()
            api = words_list[1]
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": "Can you provide information about " + api.strip('"') + " API and also provide an example of its usage?",
                        }
                    ],
                    model="gpt-3.5-turbo",
                )
                response = chat_completion.choices[0].message.content
            except Exception as e:
                response = str(e)
        else:
            response = parser.parse(prompt)
            if response == None:
                response = "Error"

        # Safely update the GUI from the main thread
        def update_gui():
            textbox.configure(state='normal')
            textbox.delete("1.0", "end")
            textbox.insert("1.0", response)
            textbox.configure(state='disabled')

        app.after(0, update_gui)

    # Start the background thread
    thread = threading.Thread(target=thread_target)
    thread.start()

def on_run_clicked():
    global uploaded_file_content
    if uploaded_file_content:
        info_textbox.configure(state='normal')
        info_textbox.delete("1.0", "end")
        info_textbox.insert("1.0", "Loading...")
        info_textbox.configure(state='disabled')
        get_response_async(uploaded_file_content, info_textbox)
    else:
        print("No file content to process")

def on_save_clicked():
    response_text = info_textbox.get("1.0", "end-1c").strip()
    if response_text:
        save_string_to_file(response_text)
    else:
        print("No response to save")

def save_string_to_file(string_to_save):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])

    if file_path:
        # Write the string to the file
        with open(file_path, 'w') as file:
            file.write(string_to_save)
        print(f"String saved to {file_path}")
    else:
        print("Save operation cancelled")

def on_upload_clicked():
    global uploaded_file_content
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
    if file_path:
        with open(file_path, 'r') as file:
            file_content = file.read()
        # Prepend "DOC" to the content of the file
        uploaded_file_content = "DOC\n" + file_content
        # Update the code editor with the DOC command
        code_editor.delete("1.0", "end")
        code_editor.insert("1.0", uploaded_file_content)
        print(f"File uploaded: {file_path}")
        print(f"File content stored in variable: {uploaded_file_content}")
    else:
        print("File upload cancelled")

# Create the main application window
app = CTk()
app.geometry("1366x768")

# Code editor setup
code_editor = CTkTextbox(master=app, width=500, height=600, corner_radius=10, border_width=2, border_color="#D1D1D1")
code_editor.place(relx=0.25, rely=0.5, anchor="center")
code_editor.configure(font=("Consolas", 12), fg_color="#F7F7F7", text_color="#333333", wrap="word")

# Info textbox setup
info_textbox = CTkTextbox(master=app, width=500, height=600, corner_radius=10, border_width=2, border_color="#D1D1D1")
info_textbox.place(relx=0.75, rely=0.5, anchor="center")
info_textbox.configure(font=("Consolas", 12), fg_color="#F7F7F7", text_color="#333333", wrap="word", state='disabled')

# Button setup
btn_run = CTkButton(master=app, text="Run", corner_radius=20,
                    fg_color="#C850C0", hover_color="#4158D0", command=on_run_clicked,
                    width=150, height=45)
btn_run.place(relx=0.5, rely=0.8, anchor="center")

btn_save = CTkButton(master=app, text="Save", corner_radius=20,
                     fg_color="#C850C0", hover_color="#4158D0", width=100, height=35, command=on_save_clicked)
btn_save.place(relx=0.75, rely=0.93, anchor="center")

btn_upload = CTkButton(master=app, text="Upload File", corner_radius=20,
                     fg_color="#C850C0", hover_color="#4158D0", width=100, height=35, command=on_upload_clicked)
btn_upload.place(relx=0.5, rely=0.6, anchor="center")

app.mainloop()
