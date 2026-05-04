import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="نظام إدارة العمارة", layout="wide")

# الرابط المختصر والـ ID الخاص بملفك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw"

# دالة التحميل المحدثة لتجنب خطأ 400
def load_data():
    try:
        # إنشاء الاتصال مع تمرير الإعدادات مباشرة لتلافي مشاكل الـ Secrets
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # محاولة القراءة مع تحديد التبويبات
        rev = conn.read(spreadsheet=SHEET_URL, worksheet="revenue", ttl=0)
        exp = conn.read(spreadsheet=SHEET_URL, worksheet="expenses", ttl=0)
        
        st.sidebar.success("✅ تم الاتصال بنجاح")
        return rev, exp
    except Exception as e:
        # إذا ظهر الخطأ 400 هنا، سنقوم بطباعة نصيحة للمستخدم
        st.error(f"❌ خطأ في تنسيق الطلب (400): {e}")
        st.info("نصيحة: تأكد من أن 'private_key' في Secrets يبدأ بـ -----BEGIN PRIVATE KEY----- وينتهي بـ \n بشكل صحيح.")
        
        # بيانات افتراضية لمنع توقف التطبيق
        r = pd.DataFrame(columns=["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"])
        e = pd.DataFrame(columns=["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])
        return r, e

revenue, expenses = load_data()
