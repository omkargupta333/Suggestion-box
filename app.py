import streamlit as st
import sqlite3
from sqlite3 import Error
from streamlit_option_menu import option_menu

st.set_page_config(
    page_icon="🌳",
    page_title="Fintree Suggestion Box"
)

# Database connection
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('fintree_suggestion_box.db')
    except Error as e:
        st.error(e)
    return conn

# Create tables
def create_tables(conn):
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                contact_number TEXT,
                suggestion_access BOOLEAN NOT NULL CHECK (suggestion_access IN (0, 1))
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        conn.commit()
    except Error as e:
        st.error(e)

# Helper functions for database operations
def add_user(conn, username, password, contact_number):
    try:
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password, contact_number, suggestion_access) VALUES (?, ?, ?, ?)', (username, password, contact_number, 0))
        conn.commit()
    except Error as e:
        st.error(e)

def get_user(conn, username):
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        return c.fetchone()
    except Error as e:
        st.error(e)
        return None

def get_all_users(conn):
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM users')
        return c.fetchall()
    except Error as e:
        st.error(e)
        return []

def update_password(conn, username, new_password):
    try:
        c = conn.cursor()
        c.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
        conn.commit()
    except Error as e:
        st.error(e)

def update_suggestion_access(conn, username, access):
    try:
        c = conn.cursor()
        c.execute('UPDATE users SET suggestion_access = ? WHERE username = ?', (access, username))
        conn.commit()
    except Error as e:
        st.error(e)

def delete_user(conn, user_id):
    try:
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
    except Error as e:
        st.error(e)

def get_all_suggestions(conn):
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM suggestions')
        return c.fetchall()
    except Error as e:
        st.error(e)
        return []

def add_suggestion(conn, username, suggestion):
    try:
        c = conn.cursor()
        c.execute('INSERT INTO suggestions (username, suggestion) VALUES (?, ?)', (username, suggestion))
        conn.commit()
    except Error as e:
        st.error(e)

def delete_suggestion(conn, suggestion_id):
    try:
        c = conn.cursor()
        c.execute('DELETE FROM suggestions WHERE id = ?', (suggestion_id,))
        conn.commit()
    except Error as e:
        st.error(e)

def admin_login(username, password):
    return username == "omadmin" and password == "ompass"

# Streamlit Application
def main():
    st.title("📮 Fintree Suggestion Box")
    
    # Database connection
    conn = create_connection()
    create_tables(conn)

    # Check if user is logged in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # Check if user is verified for password reset
    if 'verified' not in st.session_state:
        st.session_state.verified = False

    # Function to handle user login
    def user_login(username):
        st.session_state.logged_in = True
        st.session_state.username = username

    # Normal user panel
    if st.session_state.logged_in and st.session_state.username != "omadmin":
        user = get_user(conn, st.session_state.username)
        if user and user[4]:  # user[4] is the suggestion_access column
            st.subheader(f"Welcome {st.session_state.username} 🎉")
            st.warning("⚠️ Please do not use bad words or any negative language in your suggestions.")
            with st.form(key='suggestion_form'):
                suggestion = st.text_area("Enter your suggestion", key="suggestion_text")
                submit_button = st.form_submit_button(label='Submit Suggestion ✉️')
            
            if submit_button:
                if suggestion.strip() == "":
                    st.error("Suggestion cannot be empty!")
                else:
                    st.success("Thank you for your suggestion! 🎈")
                    st.balloons()
                    add_suggestion(conn, st.session_state.username, suggestion)
                    st.session_state.suggestion_submitted = True
        
        else:
            st.subheader("Access Denied")
            st.warning("Your account does not have access to the suggestion box yet. Please wait for the admin to grant access. Thank you for your patience!")
        
        if st.button("Logout", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.suggestion_submitted = False

    elif st.session_state.logged_in and st.session_state.username == "omadmin":
        # Admin panel with option menu
        with st.sidebar:
            selected = option_menu("Admin Panel", ["Admin Suggestion", "Suggestion List", "User Control"], 
                                   icons=["pencil", "list", "gear"], menu_icon="cast", default_index=0)
        
        if selected == "Admin Suggestion":
            st.subheader("Admin Suggestion")
            st.warning("⚠️ Please do not use bad words or any negative language in your suggestions.")
            with st.form(key='admin_suggestion_form'):
                admin_suggestion = st.text_area("Enter your suggestion", key="admin_suggestion_text")
                admin_submit_button = st.form_submit_button(label='Submit Suggestion ✉️')
            
            if admin_submit_button:
                st.success("Suggestion submitted successfully!")
                add_suggestion(conn, "omadmin", admin_suggestion)
                st.session_state.admin_suggestion_submitted = True
        
        elif selected == "Suggestion List":
            st.subheader("Suggestion List 📋")
            suggestions = get_all_suggestions(conn)
            suggestion_count = len(suggestions)
            st.write(f"Total Suggestions: {suggestion_count}")
            
            for idx, suggestion in enumerate(suggestions):
                with st.form(key=f'suggestion_form_{idx}'):
                    st.write(f"Suggestion: {suggestion[2]}")  # suggestion[2] is the suggestion text
                    delete_button = st.form_submit_button(label='Delete 🗑️')
                    if delete_button:
                        delete_suggestion(conn, suggestion[0])  # suggestion[0] is the suggestion ID
                        st.session_state.suggestion_deleted = True
                        break  # Break to avoid deleting multiple items in one rerun
        
        elif selected == "User Control":
            st.subheader("User Control")
            user_control_tab = st.tabs(["User Permission", "Total User"])

            with user_control_tab[0]:
                st.subheader("User Permission")
                users = get_all_users(conn)
                for user in users:
                    if user[1] != "omadmin":  # user[1] is the username
                        with st.form(key=f'user_permission_form_{user[1]}'):
                            st.write(f"Username: {user[1]}")
                            access = st.checkbox("Suggestion Access", value=user[4], key=f'access_{user[1]}')  # user[4] is the suggestion_access column
                            update_button = st.form_submit_button(label='Update Access')
                            if update_button:
                                update_suggestion_access(conn, user[1], access)
                                st.session_state.access_updated = True
                                break  # Break to avoid updating multiple items in one rerun

            with user_control_tab[1]:
                st.subheader("Total User")
                users = get_all_users(conn)
                
                for user in users:
                    if user[1] != "omadmin":  # user[1] is the username
                        with st.form(key=f'user_form_{user[1]}'):
                            st.write(f"Username: {user[1]}")
                            delete_button = st.form_submit_button(label='Delete User 🗑️')
                            if delete_button:
                                delete_user(conn, user[0])  # user[0] is the user ID
                                st.session_state.user_deleted = True
                                break  # Break to avoid deleting multiple items in one rerun
        
        if st.button("Logout", key="admin_logout_button"):
            st.session_state.logged_in = False
            st.session_state.username = ""

    else:
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Login", "Register", "Forgot Password", "Admin Login"])

        # Login Tab
        with tab1:
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_button"):
                user = get_user(conn, username)
                if user and user[2] == password:  # user[2] is the password
                    st.success(f"Welcome {username} 🎉")
                    user_login(username)
                else:
                    st.error("Invalid Username or Password")

        # Register Tab
        with tab2:
            st.subheader("Register 📝")
            new_username = st.text_input("New Username", key="register_username")
            new_password = st.text_input("New Password", type="password", key="register_password")
            contact_number = st.text_input("Contact Number", key="register_contact")
            if st.button("Register", key="register_button"):
                if not new_username or not new_password or not contact_number:
                    st.error("Please fill all fields")
                elif len(contact_number) != 10:
                    st.error("Contact Number must be 10 digits")
                else:
                    add_user(conn, new_username, new_password, contact_number)
                    st.success("You have successfully registered!")
                    user_login(new_username)

        # Forgot Password Tab
        with tab3:
            st.subheader("Forgot Password")
            if st.session_state.verified:
                new_password = st.text_input("New Password", type="password", key="forgot_new_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="forgot_confirm_password")
                if st.button("Reset Password", key="forgot_reset_button"):
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        update_password(conn, st.session_state.username, new_password)
                        st.success("Password has been reset")
                        st.session_state.verified = False  # Reset the verification state
                        st.session_state.username = ""
            else:
                username = st.text_input("Username", key="forgot_username")
                contact_number = st.text_input("Contact Number", key="forgot_contact")
                if st.button("Verify", key="forgot_verify"):
                    user = get_user(conn, username)
                    if user and user[3] == contact_number:  # user[3] is the contact_number
                        st.success("Verification successful. Please enter your new password.")
                        st.session_state.verified = True
                        st.session_state.username = username
                    else:
                        st.error("Invalid Username or Contact Number")

        # Admin Login Tab
        with tab4:
            st.subheader("Admin Login")
            admin_username = st.text_input("Admin Username", key="admin_username")
            admin_password = st.text_input("Admin Password", type="password", key="admin_password")
            if st.button("Login", key="admin_login_button"):
                if admin_login(admin_username, admin_password):
                    st.success("Welcome Admin 🎉")
                    user_login("omadmin")
                else:
                    st.error("Invalid Admin Username or Password")

if __name__ == "__main__":
    main()
