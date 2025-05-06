import streamlit as st

def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # For demo, accept any non-empty username/password
        if username and password:
            st.session_state["user"] = username
            st.success("Logged in!")
            st.experimental_rerun()
        else:
            st.error("Please enter username and password.")

def logout():
    if "user" in st.session_state:
        del st.session_state["user"]

def get_current_user():
    return st.session_state.get("user") 