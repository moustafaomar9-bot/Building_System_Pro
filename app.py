import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# إعدادات الصفحة والاتصال
st.set_page_config(page_title="نظام إدارة العمارة", layout="wide")

# تأمين المفتاح السري
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# الـ ID الخاص بملفك (تم استخراجه من الرابط الذي أرسلته)
SHEET_ID = "1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw"

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # محاولة القراءة باستخدام الـ ID مباشرة
        rev = conn.read(spreadsheet=SHEET_ID, worksheet="revenue", ttl=0)
        exp = conn.read(spreadsheet=SHEET_ID, worksheet="expenses", ttl=0)
        st.sidebar.success("✅ متصل بجوجل شيت بنجاح")
        return rev, exp
    except Exception as e:
        st.error(f"❌ لا يزال هناك خطأ في الوصول: {e}")
        # جداول افتراضية في حالة الفشل لتجنب توقف البرنامج
        r = pd.DataFrame(columns=["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"])
        e = pd.DataFrame(columns=["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])
        return r, e

revenue, expenses = load_data()

# عرض البيانات للتأكد
st.title("بيانات العمارة من جوجل شيت")
if not revenue.empty:
    st.write("بيانات الإيرادات:")
    st.dataframe(revenue)
else:
    st.warning("الجدول يظهر فارغاً. تأكد من وجود بيانات تحت العناوين في الشيت.")
