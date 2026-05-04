import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from streamlit_gsheets import GSheetsConnection

# إعداد الصفحة
st.set_page_config(page_title="نظام إدارة العمارة - النسخة السحابية", layout="wide")

# رابط الشيت الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw/edit?usp=sharing"

# =====================================================
# دالة معالجة العربي للرسوم البيانية
# =====================================================
def ar(text):
    if pd.isna(text) or text == "": return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# =====================================================
# الاتصال بجوجل شيت وتحميل البيانات
# =====================================================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # قراءة البيانات من التابات المحددة
        rev = conn.read(spreadsheet=SHEET_URL, worksheet="revenue", ttl="0")
        exp = conn.read(spreadsheet=SHEET_URL, worksheet="expenses", ttl="0")
    except Exception as e:
        st.error(f"خطأ في الاتصال بالشيت: {e}")
        rev = pd.DataFrame(columns=["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"])
        exp = pd.DataFrame(columns=["التاريخ", "النوع", "التفاصيل", "المبلغ"])
    
    # تحويل القيم لنوع عددي لضمان صحة الحسابات
    rev["الاشتراك"] = pd.to_numeric(rev["الاشتراك"], errors="coerce").fillna(0)
    rev["المدفوع"] = pd.to_numeric(rev["المدفوع"], errors="coerce").fillna(0)
    exp["المبلغ"] = pd.to_numeric(exp["المبلغ"], errors="coerce").fillna(0)
    return rev, exp

def save_all(rev_df, exp_df):
    try:
        # تحديث البيانات في جوجل شيت
        conn.update(spreadsheet=SHEET_URL, worksheet="revenue", data=rev_df)
        conn.update(spreadsheet=SHEET_URL, worksheet="expenses", data=exp_df)
        st.success("✅ تم حفظ البيانات في جوجل شيت بنجاح!")
    except Exception as e:
        st.error(f"فشل الحفظ: {e}")

# تحميل البيانات عند بدء التشغيل
revenue, expenses = load_data()

# =====================================================
# القائمة الجانبية
# =====================================================
st.sidebar.title("🏢 إدارة اتحاد الملاك")
menu = st.sidebar.radio("القائمة الرئيسية", ["لوحة التحكم", "الإيرادات", "المصاريف", "المتأخرات", "التقارير الاحترافية"])

# =====================================================
# 1. لوحة التحكم
# =====================================================
if menu == "لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    t_sub, t_paid, t_exp = revenue["الاشتراك"].sum(), revenue["المدفوع"].sum(), expenses["المبلغ"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المطلوبات", f"{int(t_sub):,}")
    c2.metric("إجمالي المحصل", f"{int(t_paid):,}")
    c3.metric("صافي الخزينة الفعلي", f"{int(t_paid - t_exp):,}")

    fig, ax = plt.subplots(figsize=(6, 2.5))
    labels = [ar("المطلوب"), ar("المحصل"), ar("المصاريف")]
    values = [t_sub, t_paid, t_exp]
    bars = ax.bar(labels, values, color=['#3498db', '#2ecc71', '#e74c3c'], width=0.5)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval, f'{int(yval):,}', ha='center', va='bottom', fontweight='bold', fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    st.pyplot(fig)

# =====================================================
# 2. الإيرادات
# =====================================================
elif menu == "الإيرادات":
    st.subheader("📥 إدارة الإيرادات")
    t1, t2 = st.tabs(["➕ إضافة جديد", "📝 تعديل"])
    with t1:
        with st.form("add_rev"):
            col1, col2, col3 = st.columns(3)
            d1, d2, d3 = col1.text_input("الدور"), col2.text_input("الوحدة"), col3.text_input("المالك")
            c4, c5, c6 = st.columns(3)
            d4 = c4.text_input("الشهر المستحق", value=datetime.now().strftime("%m/%Y"))
            d5, d6 = c5.number_input("الاشتراك", 0), c6.number_input("المدفوع", 0)
            if st.form_submit_button("حفظ وإرسال لجوجل شيت"):
                new_row = pd.DataFrame([[d1, d2, d3, d4, d5, d6, ""]], columns=revenue.columns)
                revenue = pd.concat([revenue, new_row], ignore_index=True)
                save_all(revenue, expenses)
                st.rerun()
    with t2:
        edited_rev = st.data_editor(revenue, num_rows="dynamic", key="rev_ed")
        if st.button("حفظ كافة التعديلات"):
            save_all(edited_rev, expenses)
            st.rerun()

# =====================================================
# 3. المصاريف
# =====================================================
elif menu == "المصاريف":
    st.subheader("📤 إدارة المصروفات")
    te1, te2 = st.tabs(["💸 تسجيل مصروف", "📝 تعديل"])
    with te1:
        with st.form("exp_add"):
            e_date = st.date_input("التاريخ", datetime.now())
            e_type = st.selectbox("النوع", ["نظافة", "كهرباء", "مياه", "صيانة", "أخرى"])
            e_amt = st.number_input("المبلغ", 0)
            e_det = st.text_area("التفاصيل")
            if st.form_submit_button("حفظ"):
                new_exp = pd.DataFrame([[e_date.strftime("%Y-%m-%d"), e_type, e_det, e_amt]], columns=expenses.columns)
                expenses = pd.concat([expenses, new_exp], ignore_index=True)
                save_all(revenue, expenses)
                st.rerun()
    with te2:
        edited_exp = st.data_editor(expenses, num_rows="dynamic", key="exp_ed")
        if st.button("حفظ كافة التعديلات"):
            save_all(revenue, edited_exp)
            st.rerun()

# =====================================================
# 4. المتأخرات
# =====================================================
elif menu == "المتأخرات":
    st.subheader("⚠️ كشف المتأخرات")
    revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
    late = revenue[revenue["المتبقي"] > 0].copy()
    
    if not late.empty:
        late_html = f"""
        <div style="direction: rtl; font-family: 'Segoe UI', sans-serif; padding: 25px; border: 3px solid #e74c3c; border-radius: 15px; background: white;">
            <h2 style="color: #c0392b; text-align: center;">⚠️ تنبيه هام: كشف مديونيات السكان</h2>
            <p style="text-align: center;">يرجى التكرم بسداد المتأخرات لضمان استمرار الخدمات.</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #c0392b; color: white;">
                    <th>المالك</th><th>الوحدة</th><th>الشهر</th><th>المبلغ</th>
                </tr>
                {" ".join([f"<tr><td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{r['المالك']}</td><td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{r['الوحدة']}</td><td style='border: 1px solid #ddd; padding: 10px; text-align: center;'>{r['شهر الاستحقاق']}</td><td style='border: 1px solid #ddd; padding: 10px; text-align: center; color:red; font-weight:bold;'>{int(r['المتبقي']):,}</td></tr>" for _, r in late.iterrows()])}
            </table>
        </div>
        """
        st.components.v1.html(late_html, height=500, scrolling=True)
    else:
        st.success("🎉 لا توجد متأخرات!")

# =====================================================
# 5. التقارير الاحترافية
# =====================================================
elif menu == "التقارير الاحترافية":
    st.title("📑 التقارير المالية الاحترافية")
    rep_mode = st.selectbox("نوع التقرير", ["تقرير مجمع شامل", "تقرير شهري تفصيلي"])
    sel_m = st.selectbox("اختر الشهر", sorted(revenue["شهر الاستحقاق"].unique(), reverse=True)) if rep_mode == "تقرير شهري تفصيلي" else ""

    if st.button("توليد التقرير الفاخر"):
        df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy() if sel_m else revenue.copy()
        table_title = f"📋 كشف اشتراكات الوحدات لعام/شهر {sel_m}" if sel_m else "📋 كشف اشتراكات الوحدات (شامل)"

        def get_h(row):
            d = row['الاشتراك'] - row['المدفوع']
            if d > 0: return f'<span style="color:red; font-weight:bold;">مطلوب: {int(d):,}</span>'
            elif d < 0: return f'<span style="color:green; font-weight:bold;">له: {int(abs(d)):,}</span>'
            return '<span style="color:gray;">مسدد</span>'
        
        df_r["حالة الحساب"] = df_r.apply(get_h, axis=1)
        s_t, p_t, e_t = df_r["الاشتراك"].sum(), df_r["المدفوع"].sum(), expenses["المبلغ"].sum()

        full_html = f"""
        <div style="direction: rtl; font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f0f2f5; padding: 20px; border-radius: 20px;">
            <div style="background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <div style="color: #1a2a6c; text-align: center; font-size: 28px; font-weight: bold; border-bottom: 5px solid #3498db; padding-bottom: 15px;">التقرير المالي الرسمي</div>
                <div style="display: flex; gap: 10px; margin: 20px 0; justify-content: space-around;">
                    <div style="background: #1e3c72; color: white; padding: 15px; border-radius: 10px; text-align: center; flex: 1;"><h3>المطلوب</h3><p>{int(s_t):,}</p></div>
                    <div style="background: #11998e; color: white; padding: 15px; border-radius: 10px; text-align: center; flex: 1;"><h3>المحصل</h3><p>{int(p_t):,}</p></div>
                    <div style="background: #cb2d3e; color: white; padding: 15px; border-radius: 10px; text-align: center; flex: 1;"><h3>المصاريف</h3><p>{int(e_t):,}</p></div>
                </div>
                <h3 style="color: #1a2a6c;">{table_title}</h3>
                {df_r.to_html(index=False, escape=False, classes='table')}
            </div>
        </div>
        """
        st.components.v1.html(full_html, height=800, scrolling=True)
        st.download_button("💾 تحميل التقرير (HTML)", full_html, "Official_Report.html", "text/html")
