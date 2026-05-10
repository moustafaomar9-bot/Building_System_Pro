import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from streamlit_gsheets import GSheetsConnection

# إعداد الصفحة
st.set_page_config(page_title="نظام إدارة العمارة", layout="wide")

# دالة معالجة العربي
def ar(text):
    if pd.isna(text) or text == "": 
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# رابط الجوجل شيت (بدون تعديل)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw"

# إنشاء الاتصال
@st.cache_resource
def init_connection():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

# تحميل البيانات
@st.cache_data(ttl=60)
def load_data(conn):
    if conn is None:
        return pd.DataFrame(), pd.DataFrame()
    
    revenue_columns = ["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"]
    expenses_columns = ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"]
    
    empty_rev = pd.DataFrame(columns=revenue_columns)
    empty_exp = pd.DataFrame(columns=expenses_columns)
    
    try:
        # محاولة قراءة ورقة revenue
        try:
            revenue = conn.read(worksheet="revenue", spreadsheet=SHEET_URL, ttl=0)
            if revenue.empty:
                revenue = empty_rev
            else:
                for col in revenue_columns:
                    if col not in revenue.columns:
                        revenue[col] = "" if col not in ["الاشتراك", "المدفوع"] else 0
        except Exception as e:
            st.warning(f"ورقة revenue غير موجودة: {e}")
            revenue = empty_rev
        
        # محاولة قراءة ورقة expenses
        try:
            expenses = conn.read(worksheet="expenses", spreadsheet=SHEET_URL, ttl=0)
            if expenses.empty:
                expenses = empty_exp
            else:
                for col in expenses_columns:
                    if col not in expenses.columns:
                        expenses[col] = "" if col != "المبلغ" else 0
        except Exception as e:
            st.warning(f"ورقة expenses غير موجودة: {e}")
            expenses = empty_exp
        
        return revenue, expenses
        
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return empty_rev, empty_exp

# حفظ البيانات
def save_data(conn, revenue_df, expenses_df):
    try:
        conn.update(worksheet="revenue", data=revenue_df, spreadsheet=SHEET_URL)
        conn.update(worksheet="expenses", data=expenses_df, spreadsheet=SHEET_URL)
        st.success("✅ تم حفظ البيانات بنجاح!")
        return True
    except Exception as e:
        st.error(f"❌ خطأ في الحفظ: {e}")
        return False

# تهيئة الاتصال
conn = init_connection()

# تحميل البيانات
revenue, expenses = load_data(conn)

# تنظيف البيانات
if not revenue.empty:
    revenue["شهر الاستحقاق"] = revenue["شهر الاستحقاق"].astype(str).replace(['nan', 'None', '<NA>', ''], '')
    revenue["الاشتراك"] = pd.to_numeric(revenue["الاشتراك"], errors="coerce").fillna(0)
    revenue["المدفوع"] = pd.to_numeric(revenue["المدفوع"], errors="coerce").fillna(0)
    
if not expenses.empty:
    if "الشهر" not in expenses.columns:
        expenses["الشهر"] = ""
    expenses["الشهر"] = expenses["الشهر"].astype(str).replace(['nan', 'None', '<NA>', ''], '')
    expenses["المبلغ"] = pd.to_numeric(expenses["المبلغ"], errors="coerce").fillna(0)

def get_sorted_months(df, col):
    if df.empty or col not in df.columns:
        return []
    months = [str(m) for m in df[col].unique() if str(m).strip() and str(m).lower() != 'nan' and str(m) != '']
    months = [m for m in months if m and m != '']
    return sorted(months, reverse=True)

# التحقق من وجود بيانات وعرض رسالة
if revenue.empty and conn is not None:
    st.warning("⚠️ لا توجد بيانات في جوجل شيت")
    st.info("""
    **خطوات إنشاء البيانات في جوجل شيت:**
    
    1. افتح رابط الجوجل شيت (سيتم فتحه تلقائياً)
    2. قم بإنشاء ورقتين بالاسمين: `revenue` و `expenses`
    3. في ورقة `revenue` اكتب هذه الأعمدة في الصف الأول:
       - الدور | الوحدة | المالك | شهر الاستحقاق | الاشتراك | المدفوع | ملاحظات
    4. في ورقة `expenses` اكتب هذه الأعمدة:
       - التاريخ | الشهر | النوع | التفاصيل | المبلغ
    5. شارك الجوجل شيت مع البريد الإلكتروني الذي يظهر في الخطأ أعلاه
    6. اضغط على زر "تحديث البيانات" في الشريط الجانبي
    """)

menu = st.sidebar.radio("📋 القائمة الرئيسية", ["🏠 لوحة التحكم", "💰 الإيرادات", "💸 المصاريف", "🆕 بدء شهر جديد", "⚠️ المتأخرات", "📊 التقارير"])

if menu == "🏠 لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات. قم بإنشاء البيانات في جوجل شيت أولاً")
        if st.button("📝 إنشاء بيانات تجريبية", use_container_width=True):
            sample_rev = pd.DataFrame({
                "الدور": ["الأول", "الأول", "الثاني", "الثاني", "الثالث"],
                "الوحدة": ["101", "102", "201", "202", "301"],
                "المالك": ["أحمد محمد", "سعيد علي", "محمد إبراهيم", "خالد حسن", "محمود عبدالله"],
                "شهر الاستحقاق": [datetime.now().strftime("%m/%Y")] * 5,
                "الاشتراك": [500, 500, 500, 500, 500],
                "المدفوع": [500, 250, 0, 100, 0],
                "ملاحظات": ["", "باقي 250", "غير مدفوع", "دفع 100", ""]
            })
            sample_exp = pd.DataFrame({
                "التاريخ": [datetime.now().strftime("%Y-%m-%d")] * 3,
                "الشهر": [datetime.now().strftime("%m/%Y")] * 3,
                "النوع": ["كهرباء", "نظافة", "صيانة"],
                "التفاصيل": ["فاتورة الكهرباء", "راتب العامل", "إصلاحات"],
                "المبلغ": [300, 200, 150]
            })
            if save_data(conn, sample_rev, sample_exp):
                st.rerun()
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("📅 عرض إحصائيات شهر:", all_m)
            
            df_r = revenue[revenue["شهر الاستحقاق"] == sel_m]
            df_e = expenses[expenses["الشهر"] == sel_m] if not expenses.empty else pd.DataFrame()
            
            t_sub = df_r["الاشتراك"].sum()
            t_paid = df_r["المدفوع"].sum()
            t_exp = df_e["المبلغ"].sum() if not df_e.empty else 0
            net = t_paid - t_exp
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 المطلوب", f"{int(t_sub):,} جنيه")
            col2.metric("✅ المحصل", f"{int(t_paid):,} جنيه")
            col3.metric("💸 المصاريف", f"{int(t_exp):,} جنيه")
            col4.metric("📈 صافي الربح", f"{int(net):,} جنيه")
            
            fig, ax = plt.subplots(figsize=(10, 5))
            categories = [ar("المطلوب"), ar("المحصل"), ar("المصاريف")]
            values = [t_sub, t_paid, t_exp]
            colors = ['#3498db', '#2ecc71', '#e74c3c']
            bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=2)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, f'{int(val):,}', ha='center', va='bottom', fontweight='bold', fontsize=12)
            ax.set_ylabel("القيمة (جنيه)", fontsize=12)
            ax.set_title(f"🏢 الملخص المالي لشهر {sel_m}", fontsize=16, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            
            with st.expander("📋 تفاصيل الإيرادات"):
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                df_r["الحالة"] = df_r["المتبقي"].apply(lambda x: "🔴 متأخر" if x > 0 else "🟢 مدفوع")
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي", "الحالة", "ملاحظات"]], use_container_width=True)
            
            if not df_e.empty:
                with st.expander("💸 تفاصيل المصروفات"):
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
        else:
            st.info("لا توجد شهور مسجلة")

elif menu == "💰 الإيرادات":
    st.title("💰 جدول الإيرادات")
    
    if revenue.empty:
        st.warning("⚠️ لا توجد بيانات إيرادات")
    else:
        st.dataframe(revenue, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        total_required = revenue['الاشتراك'].sum()
        total_paid = revenue['المدفوع'].sum()
        col1.metric("اجمالي المطلوب", f"{int(total_required):,} جنيه")
        col2.metric("اجمالي المحصل", f"{int(total_paid):,} جنيه")
        col3.metric("المتبقي", f"{int(total_required - total_paid):,} جنيه")

elif menu == "💸 المصاريف":
    st.title("💸 جدول المصروفات")
    
    if expenses.empty:
        st.warning("⚠️ لا توجد بيانات مصروفات")
    else:
        st.dataframe(expenses, use_container_width=True)
        total_exp = expenses['المبلغ'].sum()
        st.metric("اجمالي المصروفات", f"{int(total_exp):,} جنيه")
        
        if 'النوع' in expenses.columns:
            exp_by_type = expenses.groupby('النوع')['المبلغ'].sum().sort_values(ascending=False)
            st.bar_chart(exp_by_type)

elif menu == "🆕 بدء شهر جديد":
    st.title("🆕 ترحيل البيانات لشهر جديد")
    
    if revenue.empty:
        st.warning("لا توجد بيانات سابقة للترحيل")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            last_m = st.selectbox("نسخ البيانات من شهر:", all_m)
            new_m = st.text_input("الشهر الجديد (مثال: 03/2026):", datetime.now().strftime("%m/%Y"))
            
            if st.button("تنفيذ الترحيل", use_container_width=True):
                if new_m in all_m:
                    st.error(f"الشهر {new_m} موجود بالفعل")
                elif new_m:
                    last_data = revenue[revenue["شهر الاستحقاق"] == last_m].copy()
                    new_rows = []
                    for _, row in last_data.iterrows():
                        debt = row["الاشتراك"] - row["المدفوع"]
                        note = f"متأخرات من {last_m}: {int(debt)}" if debt > 0 else "مسدد"
                        new_rows.append([row["الدور"], row["الوحدة"], row["المالك"], new_m, row["الاشتراك"], 0, note])
                    new_month_data = pd.DataFrame(new_rows, columns=revenue.columns)
                    updated_revenue = pd.concat([revenue, new_month_data], ignore_index=True)
                    if save_data(conn, updated_revenue, expenses):
                        st.balloons()
                        st.rerun()

elif menu == "⚠️ المتأخرات":
    st.title("⚠️ كشف المتأخرات")
    
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
        late = revenue[revenue["المتبقي"] > 0].copy()
        
        if not late.empty:
            total_late = late["المتبقي"].sum()
            col1, col2 = st.columns(2)
            col1.metric("💰 اجمالي المتأخرات", f"{int(total_late):,} جنيه")
            col2.metric("📊 عدد الوحدات المتأخرة", f"{len(late)} وحدة")
            
            late_display = late[["المالك", "الوحدة", "الدور", "شهر الاستحقاق", "الاشتراك", "المدفوع", "المتبقي", "ملاحظات"]]
            late_display = late_display.sort_values("المتبقي", ascending=False)
            st.dataframe(late_display, use_container_width=True)
        else:
            st.success("🎉 لا توجد متأخرات! جميع الوحدات مسددة بالكامل.")
            st.balloons()

elif menu == "📊 التقارير":
    st.title("📊 التقارير المالية")
    
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("📅 اختر الشهر للتقرير:", all_m)
            df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
            df_e = expenses[expenses["الشهر"] == sel_m].copy() if not expenses.empty else pd.DataFrame()
            
            if st.button("📄 توليد التقرير", use_container_width=True):
                total_required = df_r["الاشتراك"].sum()
                total_paid = df_r["المدفوع"].sum()
                total_expenses = df_e["المبلغ"].sum() if not df_e.empty else 0
                net_profit = total_paid - total_expenses
                payment_rate = (total_paid / total_required * 100) if total_required > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("المطلوب", f"{int(total_required):,} جنيه")
                col2.metric("المحصل", f"{int(total_paid):,} جنيه")
                col3.metric("المصاريف", f"{int(total_expenses):,} جنيه")
                col4.metric("صافي الربح", f"{int(net_profit):,} جنيه")
                
                st.progress(payment_rate / 100)
                st.caption(f"نسبة التحصيل: {payment_rate:.1f}%")
                
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي"]], use_container_width=True)
                
                if not df_e.empty:
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
                
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(['المطلوب', 'المحصل', 'المصاريف'], [total_required, total_paid, total_expenses], color=['#3498db', '#2ecc71', '#e74c3c'])
                ax.set_ylabel('القيمة (جنيه)')
                ax.set_title(f'ملخص شهر {sel_m}')
                st.pyplot(fig)
        else:
            st.info("لا توجد شهور مسجلة")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("📝 إنشاء بيانات تجريبية", use_container_width=True):
    sample_rev = pd.DataFrame({
        "الدور": ["الأول", "الأول", "الثاني", "الثاني", "الثالث"],
        "الوحدة": ["101", "102", "201", "202", "301"],
        "المالك": ["أحمد محمد", "سعيد علي", "محمد إبراهيم", "خالد حسن", "محمود عبدالله"],
        "شهر الاستحقاق": [datetime.now().strftime("%m/%Y")] * 5,
        "الاشتراك": [500, 500, 500, 500, 500],
        "المدفوع": [500, 250, 0, 100, 0],
        "ملاحظات": ["", "باقي 250", "غير مدفوع", "دفع 100", ""]
    })
    sample_exp = pd.DataFrame({
        "التاريخ": [datetime.now().strftime("%Y-%m-%d")] * 3,
        "الشهر": [datetime.now().strftime("%m/%Y")] * 3,
        "النوع": ["كهرباء", "نظافة", "صيانة"],
        "التفاصيل": ["فاتورة الكهرباء", "راتب العامل", "إصلاحات"],
        "المبلغ": [300, 200, 150]
    })
    if save_data(conn, sample_rev, sample_exp):
        st.rerun()
