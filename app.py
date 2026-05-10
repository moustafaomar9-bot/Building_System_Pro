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

# رابط الجوجل شيت
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw"

# إنشاء الاتصال
def get_connection():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

# دالة لإعادة تسمية الأعمدة بشكل صحيح
def fix_columns(df, expected_columns, sheet_name):
    if df.empty:
        return df
    
    # محاولة العثور على الأعمدة المطلوبة بغض النظر عن الترتيب
    column_mapping = {}
    for col in expected_columns:
        # البحث عن عمود يحتوي على الاسم (قد يكون هناك اختلاف في التشكيل)
        found = None
        for existing_col in df.columns:
            if col in existing_col or existing_col in col:
                found = existing_col
                break
        if found:
            column_mapping[found] = col
        else:
            # إذا لم نجد العمود، نضيفه كعمود فارغ
            df[col] = ""
    
    # إعادة تسمية الأعمدة
    df = df.rename(columns=column_mapping)
    
    # التأكد من وجود جميع الأعمدة المطلوبة
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""
    
    # إرجاع الأعمدة بالترتيب المطلوب فقط
    return df[expected_columns]

# تحميل البيانات
@st.cache_data(ttl=60)
def load_data():
    revenue_columns = ["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"]
    expenses_columns = ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"]
    
    empty_rev = pd.DataFrame(columns=revenue_columns)
    empty_exp = pd.DataFrame(columns=expenses_columns)
    
    try:
        conn = get_connection()
        if conn is None:
            return empty_rev, empty_exp
        
        # محاولة قراءة ورقة revenue
        try:
            revenue = conn.read(worksheet="revenue", spreadsheet=SHEET_URL, ttl=0)
            st.write("تم قراءة البيانات بنجاح، عدد الصفوف:", len(revenue))
            st.write("الأعمدة الموجودة:", list(revenue.columns))
            
            if revenue.empty:
                revenue = empty_rev
            else:
                # إعادة ترتيب الأعمدة
                revenue = fix_columns(revenue, revenue_columns, "revenue")
                
        except Exception as e:
            st.warning(f"خطأ في قراءة ورقة revenue: {str(e)}")
            revenue = empty_rev
        
        # محاولة قراءة ورقة expenses
        try:
            expenses = conn.read(worksheet="expenses", spreadsheet=SHEET_URL, ttl=0)
            if expenses.empty:
                expenses = empty_exp
            else:
                expenses = fix_columns(expenses, expenses_columns, "expenses")
        except Exception as e:
            st.warning(f"خطأ في قراءة ورقة expenses: {str(e)}")
            expenses = empty_exp
        
        return revenue, expenses
        
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
        return empty_rev, empty_exp

# حفظ البيانات
def save_data(revenue_df, expenses_df):
    try:
        conn = get_connection()
        if conn is None:
            return False
        conn.update(worksheet="revenue", data=revenue_df, spreadsheet=SHEET_URL)
        conn.update(worksheet="expenses", data=expenses_df, spreadsheet=SHEET_URL)
        st.success("✅ تم حفظ البيانات بنجاح!")
        return True
    except Exception as e:
        st.error(f"❌ خطأ في الحفظ: {e}")
        return False

# تحميل البيانات
revenue, expenses = load_data()

# عرض حالة البيانات في الشريط الجانبي
st.sidebar.info(f"📊 عدد صفوف الإيرادات: {len(revenue)}")
st.sidebar.info(f"📊 عدد صفوف المصروفات: {len(expenses)}")

# تنظيف البيانات
if not revenue.empty:
    # تحويل الأعمدة الرقمية
    revenue["الاشتراك"] = pd.to_numeric(revenue["الاشتراك"], errors="coerce").fillna(0)
    revenue["المدفوع"] = pd.to_numeric(revenue["المدفوع"], errors="coerce").fillna(0)
    revenue["شهر الاستحقاق"] = revenue["شهر الاستحقاق"].astype(str).str.strip()
    
    # تنظيف الأرقام غير الصحيحة في الشهور
    revenue["شهر الاستحقاق"] = revenue["شهر الاستحقاق"].apply(lambda x: x if "/202" in str(x) or "/202" in str(x) else "")
    
    # عرض معاينة للبيانات
    with st.sidebar.expander("معاينة البيانات المستخرجة"):
        st.write(revenue.head(10))
    
if not expenses.empty:
    expenses["المبلغ"] = pd.to_numeric(expenses["المبلغ"], errors="coerce").fillna(0)
    expenses["الشهر"] = expenses["الشهر"].astype(str).str.strip()

def get_sorted_months(df, col):
    if df.empty or col not in df.columns:
        return []
    months = [str(m) for m in df[col].unique() if str(m).strip() and str(m).lower() != 'nan' and str(m) != '' and len(str(m)) > 5]
    months = [m for m in months if m and m != '']
    return sorted(months, reverse=True)

# عرض رسالة للمستخدم
if revenue.empty:
    st.warning("⚠️ لم يتم العثور على بيانات في ورقة revenue")
    st.info("""
    **تأكد من:**
    1. أن ورقة العمل في جوجل شيت اسمها `revenue` (وليس `ورقة1` أو غيره)
    2. أن الأعمدة تحتوي على عناوين مناسبة (دور, وحدة, مالك, شهر الاستحقاق, اشتراك, مدفوع)
    3. أن حساب الخدمة phone-952@phoneproject.iam.gserviceaccount.com لديه صلاحية محرر على الجوجل شيت
    """)
else:
    st.success(f"✅ تم تحميل {len(revenue)} سجل من الإيرادات بنجاح!")

menu = st.sidebar.radio("📋 القائمة الرئيسية", ["🏠 لوحة التحكم", "💰 الإيرادات", "💸 المصروفات", "🆕 بدء شهر جديد", "⚠️ المتأخرات", "📊 التقارير"])

if menu == "🏠 لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات لعرضها")
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
            
            if not df_r.empty:
                st.subheader("📋 تفاصيل الإيرادات")
                df_r_display = df_r.copy()
                df_r_display["المتبقي"] = df_r_display["الاشتراك"] - df_r_display["المدفوع"]
                df_r_display["الحالة"] = df_r_display["المتبقي"].apply(lambda x: "🔴 متأخر" if x > 0 else "🟢 مدفوع")
                st.dataframe(df_r_display[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي", "الحالة", "ملاحظات"]], use_container_width=True)
            
            if not df_e.empty:
                st.subheader("💸 تفاصيل المصروفات")
                st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
        else:
            st.info("لا توجد شهور صالحة في البيانات. تأكد من أن شهر الاستحقاق مكتوب بشكل صحيح (مثال: 02/2026)")

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

elif menu == "💸 المصروفات":
    st.title("💸 جدول المصروفات")
    
    if expenses.empty:
        st.warning("⚠️ لا توجد بيانات مصروفات")
    else:
        st.dataframe(expenses, use_container_width=True)
        total_exp = expenses['المبلغ'].sum()
        st.metric("اجمالي المصروفات", f"{int(total_exp):,} جنيه")

elif menu == "🆕 بدء شهر جديد":
    st.title("🆕 ترحيل البيانات لشهر جديد")
    
    if revenue.empty:
        st.warning("لا توجد بيانات سابقة للترحيل")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            last_m = st.selectbox("نسخ البيانات من شهر:", all_m)
            new_m = st.text_input("الشهر الجديد (مثال: 04/2026):", datetime.now().strftime("%m/%Y"))
            
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
                    if save_data(updated_revenue, expenses):
                        st.cache_data.clear()
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
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("المطلوب", f"{int(total_required):,} جنيه")
                col2.metric("المحصل", f"{int(total_paid):,} جنيه")
                col3.metric("المصاريف", f"{int(total_expenses):,} جنيه")
                col4.metric("صافي الربح", f"{int(net_profit):,} جنيه")
                
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي"]], use_container_width=True)
        else:
            st.info("لا توجد شهور صالحة")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
