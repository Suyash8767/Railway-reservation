import streamlit as st
import sqlite3
import random
import time
from datetime import date

# ---------------- DATABASE ----------------
conn = sqlite3.connect("railway.db", check_same_thread=False)
cursor = conn.cursor()

# trains
cursor.execute("""
CREATE TABLE IF NOT EXISTS trains(
train_no INTEGER PRIMARY KEY,
name TEXT,
source TEXT,
destination TEXT
)
""")

# seats per coach
cursor.execute("""
CREATE TABLE IF NOT EXISTS seats(
train_no INTEGER,
coach TEXT,
seat_no INTEGER,
status TEXT
)
""")

# bookings
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings(
pnr INTEGER PRIMARY KEY,
name TEXT,
train_no INTEGER,
coach TEXT,
seat_no TEXT,
status TEXT,
travel_date TEXT
)
""")

# default trains
cursor.execute("INSERT OR IGNORE INTO trains VALUES(101,'Express','Mumbai','Pune')")
cursor.execute("INSERT OR IGNORE INTO trains VALUES(102,'Superfast','Pune','Nagpur')")

# create seats (20 seats each coach)
for train in [101,102]:
    for coach in ["SL","3AC","2AC","1AC"]:
        for seat in range(1,21):
            cursor.execute(
                "INSERT OR IGNORE INTO seats VALUES(?,?,?,?)",
                (train,coach,seat,"FREE")
            )

conn.commit()

# ---------------- UI ----------------
st.title("🚆 Smart Railway Reservation")

menu = st.sidebar.selectbox("Menu",["Search Train","Book Ticket","View Ticket"])

# ---------------- SEARCH ----------------
if menu=="Search Train":

    source = st.text_input("From")
    dest = st.text_input("To")

    if st.button("Search"):
        with st.spinner("Searching trains..."):
            time.sleep(1.2)

        trains = cursor.execute(
            "SELECT * FROM trains WHERE source=? AND destination=?",
            (source,dest)
        ).fetchall()

        if trains:
            for t in trains:
                st.success(f"{t[1]} (Train {t[0]})")
        else:
            st.error("No trains found")

# ---------------- BOOK ----------------
elif menu=="Book Ticket":

    st.header("🎫 Select Seat & Book")

    name = st.text_input("Passenger Name")
    train_no = st.number_input("Train Number", step=1)
    coach = st.selectbox("Coach",["SL","3AC","2AC","1AC"])
    travel_date = st.date_input("Travel Date",min_value=date.today())

    seat_choice = st.number_input("Preferred Seat Number (1-20)",1,20)

    if st.button("Check Seat"):
        with st.spinner("Checking seat..."):
            time.sleep(1)

        seat = cursor.execute(
            "SELECT status FROM seats WHERE train_no=? AND coach=? AND seat_no=?",
            (train_no,coach,seat_choice)
        ).fetchone()

        if seat and seat[0]=="FREE":
            st.success("Seat Available ✔")
        else:
            st.error("Seat Not Available ❌")

            # suggest nearby seats
            alt = cursor.execute(
                "SELECT seat_no FROM seats WHERE train_no=? AND coach=? AND status='FREE' LIMIT 5",
                (train_no,coach)
            ).fetchall()

            if alt:
                st.info("Suggested Seats: " + ", ".join(str(a[0]) for a in alt))
            else:
                st.warning("Coach Full — RAC/WL applicable")

    if st.button("Confirm Booking"):

        with st.spinner("Booking ticket..."):
            time.sleep(2)

        pnr = random.randint(100000,999999)

        seat = cursor.execute(
            "SELECT status FROM seats WHERE train_no=? AND coach=? AND seat_no=?",
            (train_no,coach,seat_choice)
        ).fetchone()

        # CONFIRMED
        if seat and seat[0]=="FREE":
            status="CONFIRMED"
            seat_no=str(seat_choice)

            cursor.execute(
                "UPDATE seats SET status='BOOKED' WHERE train_no=? AND coach=? AND seat_no=?",
                (train_no,coach,seat_choice)
            )

        else:
            # RAC
            rac_count = cursor.execute(
                "SELECT COUNT(*) FROM bookings WHERE train_no=? AND coach=? AND status='RAC'",
                (train_no,coach)
            ).fetchone()[0]

            wl_count = cursor.execute(
                "SELECT COUNT(*) FROM bookings WHERE train_no=? AND coach=? AND status='WAITING'",
                (train_no,coach)
            ).fetchone()[0]

            if rac_count < 2:
                status="RAC"
                seat_no=f"RAC{rac_count+1}"
            else:
                status="WAITING"
                seat_no=f"WL{wl_count+1}"

        cursor.execute(
            "INSERT INTO bookings VALUES(?,?,?,?,?,?,?)",
            (pnr,name,train_no,coach,seat_no,status,str(travel_date))
        )

        conn.commit()

        st.success(f"PNR: {pnr}")
        st.write(f"Seat: {seat_no}")
        st.write(f"Status: {status}")

# ---------------- VIEW ----------------
elif menu=="View Ticket":

    pnr = st.number_input("Enter PNR", step=1)

    if st.button("Search"):
        ticket = cursor.execute(
            "SELECT * FROM bookings WHERE pnr=?",
            (pnr,)
        ).fetchone()

        if ticket:
            st.success("Ticket Found")
            st.write("Name:",ticket[1])
            st.write("Train:",ticket[2])
            st.write("Coach:",ticket[3])
            st.write("Seat:",ticket[4])
            st.write("Status:",ticket[5])
            st.write("Date:",ticket[6])
        else:
            st.error("Invalid PNR")
            st.caption("- made by Cm4K A")