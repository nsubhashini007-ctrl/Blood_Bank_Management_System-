import streamlit as st
import mysql.connector
import pandas as pd
import altair as alt
from datetime import date

# ---------------- LOGIN SYSTEM ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Blood Bank Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.success("✅ Login Successful")
        else:
            st.error("❌ Invalid Credentials")

# ---------------- DATABASE CONNECTION ----------------
def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Subhashini@2007",
            database="blood_bank"
        )
        return db
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

# ---------------- MAIN APP ----------------
def main():
    db = connect_db()
    cursor = db.cursor()

    st.title("🩸 Centralized Blood Bank Management System")
    
    # Logout
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    menu = [
        "Dashboard",
        "Add Donor",
        "Add Hospital",
        "Add Recipient",
        "View Data",
        "Search Donor",
        "Update Blood Stock"
    ]
    choice = st.sidebar.radio("Menu", menu)

    # ---------------- DASHBOARD ----------------
    if choice == "Dashboard":
        st.subheader("📊 Dashboard")

        # Total Counts
        cursor.execute("SELECT COUNT(*) FROM Donor")
        total_donors = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Recipient")
        total_recipients = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Hospital")
        total_hospitals = cursor.fetchone()[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("🧑 Total Donors", total_donors)
        col2.metric("🧑‍🩺 Total Recipients", total_recipients)
        col3.metric("🏥 Total Hospitals", total_hospitals)

        # Donor Age Distribution
        cursor.execute("SELECT age, gender FROM Donor")
        data = cursor.fetchall()
        if data:
            df_donor = pd.DataFrame(data, columns=["Age", "Gender"])
            chart = alt.Chart(df_donor).mark_bar().encode(
                x='Age:Q',
                y='count()',
                color='Gender:N'
            ).properties(title="Donor Age Distribution")
            st.altair_chart(chart, use_container_width=True)

        # Donor Blood Group Counts
        cursor.execute("SELECT blood_group, COUNT(*) FROM Donor GROUP BY blood_group")
        data = cursor.fetchall()
        if data:
            df_bg = pd.DataFrame(data, columns=["Blood Group", "Count"])
            chart2 = alt.Chart(df_bg).mark_bar().encode(
                x='Blood Group:N',
                y='Count:Q',
                color='Blood Group:N'
            ).properties(title="Donor Blood Group Counts")
            st.altair_chart(chart2, use_container_width=True)

        # Blood Stock Chart
        cursor.execute("SELECT blood_group, available_units FROM blood_stock")
        stock_data = cursor.fetchall()
        if stock_data:
            df_stock = pd.DataFrame(stock_data, columns=["Blood Group", "Units Available"])
            st.write("### 🩸 Blood Stock")
            chart_stock = alt.Chart(df_stock).mark_bar().encode(
                x='Blood Group:N',
                y='Units Available:Q',
                color='Blood Group:N'
            ).properties(title="Available Blood Units by Group")
            st.altair_chart(chart_stock, use_container_width=True)

    # ---------------- ADD DONOR ----------------
    elif choice == "Add Donor":
        st.subheader("➕ Add Donor")
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=18, max_value=60)
        gender = st.selectbox("Gender", ["Male", "Female"])
        blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        phone = st.text_input("Phone Number")
        last_date = st.date_input("Last Donation Date", max_value=date.today())

        if st.button("Add Donor"):
            if name and phone:
                cursor.execute("""INSERT INTO Donor 
                                (name, age, gender, blood_group, phone_number, last_donation_date) 
                                VALUES (%s,%s,%s,%s,%s,%s)""",
                               (name, age, gender, blood, phone, last_date))
                # Update blood stock
                cursor.execute("UPDATE blood_stock SET available_units = available_units + 1 WHERE blood_group=%s", (blood,))
                db.commit()
                st.success("✅ Donor Added Successfully! Blood stock updated!")
            else:
                st.warning("⚠️ Please fill all fields")

    # ---------------- ADD HOSPITAL ----------------
    elif choice == "Add Hospital":
        st.subheader("🏥 Add Hospital")
        h_name = st.text_input("Hospital Name")
        location = st.text_input("Location")
        contact = st.text_input("Contact Number")

        if st.button("Add Hospital"):
            if h_name and contact:
                cursor.execute("INSERT INTO Hospital (hospital_name, location, contact_number) VALUES (%s,%s,%s)",
                               (h_name, location, contact))
                db.commit()
                st.success("✅ Hospital Added Successfully!")
            else:
                st.warning("⚠️ Fill all fields")

    # ---------------- ADD RECIPIENT ----------------
    elif choice == "Add Recipient":
        st.subheader("🧑‍🩺 Add Recipient")
        r_name = st.text_input("Recipient Name")
        blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

        cursor.execute("SELECT hospital_id, hospital_name FROM Hospital")
        hospitals = cursor.fetchall()

        if hospitals:
            hospital_dict = {h[1]: h[0] for h in hospitals}
            hospital_name = st.selectbox("Select Hospital", list(hospital_dict.keys()))
            hospital_id = hospital_dict[hospital_name]

            if st.button("Add Recipient"):
                if r_name:
                    cursor.execute("INSERT INTO Recipient (name, blood_group, hospital_id) VALUES (%s,%s,%s)",
                                   (r_name, blood, hospital_id))
                    # Reduce blood stock if available
                    cursor.execute("""UPDATE blood_stock 
                                      SET available_units = available_units - 1 
                                      WHERE blood_group=%s AND available_units > 0""", (blood,))
                    db.commit()
                    st.success("✅ Recipient Added Successfully! Blood stock updated!")
                else:
                    st.warning("⚠️ Enter recipient name")
        else:
            st.warning("⚠️ Please add Hospital first")

    # ---------------- VIEW DATA ----------------
    elif choice == "View Data":
        st.subheader("📊 Centralized Database View")

        # Donors
        cursor.execute("SELECT * FROM Donor")
        donors = cursor.fetchall()
        df_donor = pd.DataFrame(donors, columns=["ID", "Name", "Age", "Gender", "Blood Group", "Phone", "Last Donation Date"])
        st.write("### 🧑 Donors")
        st.dataframe(df_donor, use_container_width=True)

        # Hospitals
        cursor.execute("SELECT * FROM Hospital")
        hospitals = cursor.fetchall()
        df_hospital = pd.DataFrame(hospitals, columns=["ID", "Hospital Name", "Location", "Contact"])
        st.write("### 🏥 Hospitals")
        st.dataframe(df_hospital, use_container_width=True)

        # Recipients
        cursor.execute("""SELECT r.recipient_id, r.name, r.blood_group, h.hospital_name
                          FROM Recipient r JOIN Hospital h ON r.hospital_id = h.hospital_id""")
        data = cursor.fetchall()
        df_recipient = pd.DataFrame(data, columns=["ID", "Name", "Blood Group", "Hospital Name"])
        st.write("### 🧑‍🩺 Recipients")
        st.dataframe(df_recipient, use_container_width=True)

        # Blood Stock
        cursor.execute("SELECT blood_group, available_units FROM blood_stock")
        stock_data = cursor.fetchall()
        df_stock = pd.DataFrame(stock_data, columns=["Blood Group", "Units Available"])
        st.write("### 🩸 Blood Stock")
        st.dataframe(df_stock, use_container_width=True)

    # ---------------- SEARCH DONOR ----------------
    elif choice == "Search Donor":
        st.subheader("🔍 Search Donor")
        bg = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        if st.button("Search"):
            cursor.execute("SELECT * FROM Donor WHERE blood_group=%s", (bg,))
            result = cursor.fetchall()
            df = pd.DataFrame(result, columns=["ID", "Name", "Age", "Gender", "Blood Group", "Phone", "Last Donation Date"])
            st.dataframe(df, use_container_width=True)

    # ---------------- UPDATE BLOOD STOCK ----------------
    elif choice == "Update Blood Stock":
        st.subheader("🩸 Update Blood Stock")
        cursor.execute("SELECT blood_group, available_units FROM blood_stock")
        stock_data = cursor.fetchall()
        blood_dict = {row[0]: row[1] for row in stock_data}
        
        bg = st.selectbox("Select Blood Group", list(blood_dict.keys()))
        units = st.number_input("Units to Add/Subtract (+/-)", value=0, step=1)
        
        if st.button("Update Stock"):
            new_units = blood_dict[bg] + units
            if new_units < 0:
                st.warning("⚠️ Cannot reduce below 0")
            else:
                cursor.execute("UPDATE blood_stock SET available_units=%s WHERE blood_group=%s", (new_units, bg))
                db.commit()
                st.success(f"✅ Stock updated for {bg}. New units: {new_units}")

# ---------------- RUN ----------------
if not st.session_state.logged_in:
    login()
else:
    main()