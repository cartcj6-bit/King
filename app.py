import json
import os
from datetime import datetime

import streamlit as st


st.set_page_config(page_title="BudgetBuddy", page_icon="🎓", layout="wide")
st.html('<meta name="google-site-verification" content="PASTE_YOUR_GOOGLE_CODE_HERE" />')

DATA_FILE = "budget_buddy_web_data.json"
CATEGORIES = ["Food", "Transportation", "School", "Wants", "Others"]


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            loaded = json.load(file)
            loaded.setdefault("allowance", 0.0)
            loaded.setdefault("expenses", [])
            return loaded
    return {"allowance": 0.0, "expenses": []}


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


def money(amount):
    return f"P{amount:,.2f}"


if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
expenses = data["expenses"]
total_spent = sum(item["amount"] for item in expenses)
remaining_balance = data["allowance"] - total_spent
spending_percent = (total_spent / data["allowance"] * 100) if data["allowance"] else 0

st.markdown(
    """
    <style>
    .stApp { background: #f6f8f7; }
    .block-container { max-width: 1180px; padding-top: 2.5rem; }
    .hero { background: linear-gradient(120deg, #123b35, #1f6656); color: white; padding: 2rem 2.2rem; border-radius: 18px; margin-bottom: 1.5rem; }
    .hero h1 { font-size: 2.6rem; margin: 0; letter-spacing: -1px; }
    .hero p { color: #d8eee7; margin: .45rem 0 0; font-size: 1.05rem; }
    [data-testid="stMetric"] { background: white; border: 1px solid #e1e9e5; padding: 1rem; border-radius: 12px; }
    .tip { background: #fff4d9; border-left: 4px solid #e5a72e; padding: .8rem 1rem; border-radius: 8px; color: #624b13; }

    @media (max-width: 640px) {
        .block-container { padding: 1rem .8rem 2rem; }
        .hero { padding: 1.35rem 1.1rem; border-radius: 12px; margin-bottom: 1rem; }
        .hero h1 { font-size: 2rem; }
        .hero p { font-size: .95rem; }
        [data-testid="stMetric"] { padding: .7rem; }
        [data-testid="stMetricValue"] { font-size: 1.25rem; }
        [data-testid="stHorizontalBlock"] { gap: .6rem; }
        .stButton > button, .stFormSubmitButton > button { min-height: 2.75rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>BudgetBuddy</h1><p>Your simple money dashboard for student life.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Budget setup")
    st.caption("Set the total money available for this budget period.")
    allowance_input = st.number_input(
        "Budget amount (P)", min_value=0.0, value=float(data["allowance"]), step=50.0
    )
    if st.button("Update budget", use_container_width=True, type="primary"):
        data["allowance"] = allowance_input
        save_data(data)
        st.success("Budget updated.")
        st.rerun()
    st.divider()
    st.markdown("### Quick guide")
    st.caption("Log small purchases as they happen. Your remaining balance will update instantly.")

st.markdown("### At a glance")
metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Budget", money(data["allowance"]))
metric_two.metric("Spent", money(total_spent))
metric_three.metric("Left to spend", money(remaining_balance), delta=f"{spending_percent:.0f}% used")
metric_four.metric("Transactions", len(expenses))

if remaining_balance < 0:
    st.error(f"You are {money(abs(remaining_balance))} over budget. Review your Wants and Food spending.")
elif data["allowance"] and spending_percent >= 80:
    st.warning(f"You have used {spending_percent:.0f}% of your budget. Keep some money aside for surprises.")
elif not data["allowance"]:
    st.info("Set your budget in the sidebar to start tracking your balance.")

st.divider()
entry_col, chart_col = st.columns([0.9, 1.1], gap="large")

with entry_col:
    st.markdown("### Add a transaction")
    with st.form("expense_form", clear_on_submit=True):
        expense_cat = st.selectbox("Category", CATEGORIES)
        expense_amt = st.number_input("Amount (P)", min_value=0.0, step=10.0)
        expense_note = st.text_input("What was it for?", placeholder="e.g. lunch after class")
        submitted = st.form_submit_button("Log expense", use_container_width=True, type="primary")
        if submitted:
            if expense_amt <= 0:
                st.error("Enter an amount greater than zero.")
            else:
                expenses.append(
                    {
                        "category": expense_cat,
                        "amount": expense_amt,
                        "note": expense_note.strip() or "No note",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                )
                save_data(data)
                st.success(f"Logged {money(expense_amt)} for {expense_cat}.")
                st.rerun()

    if data["allowance"] and remaining_balance > 0:
        daily_guide = remaining_balance / 30
        st.markdown(
            f'<div class="tip"><strong>Spending guide</strong><br>You have about {money(daily_guide)} per day if this budget lasts 30 days.</div>',
            unsafe_allow_html=True,
        )

with chart_col:
    st.markdown("### Where your money goes")
    if expenses:
        category_summary = {category: 0.0 for category in CATEGORIES}
        for expense in expenses:
            category_summary[expense["category"]] = category_summary.get(expense["category"], 0.0) + expense["amount"]
        category_summary = {category: amount for category, amount in category_summary.items() if amount > 0}
        st.bar_chart(category_summary, color="#287c67", height=280)
        top_category, top_amount = max(category_summary.items(), key=lambda item: item[1])
        st.caption(f"Your biggest category is **{top_category}** at {money(top_amount)}.")
    else:
        st.info("Your spending chart will appear after your first transaction.")

st.divider()
st.markdown("### Recent transactions")
if expenses:
    for index, expense in sorted(enumerate(expenses), key=lambda item: item[1]["date"], reverse=True):
        row_one, row_two, row_three, row_four = st.columns([1.3, 2.1, 1.1, 0.55])
        row_one.caption(expense["date"])
        row_two.write(f"**{expense['category']}** · {expense.get('note', 'No note')}")
        row_three.write(f"**{money(expense['amount'])}**")
        if row_four.button("Delete", key=f"delete_{index}"):
            expenses.pop(index)
            save_data(data)
            st.rerun()
else:
    st.info("No transactions yet. Add your first expense above.")
