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

# دالة للحصول على جميع أسماء الأوراق في الجوجل شيت
def get_all_worksheets(conn):
    try:
        # قراءة البيانات بدون تحديد ورقة للحصول على معلومات الأوراق
        spread = conn.read(spreadsheet=SHEET_URL, worksheet=None)
        if hasattr(spread, 'keys'):
            return list(spread.keys())
    except:
        pass
    return []

# تحميل البيانات
@st.cache_data(ttl=60)
def load_data():
    empty_rev = pd.DataFrame()
    empty_exp = pd.DataFrame()
    
    try:
        conn = get_connection()
        if conn is None:
            return empty_rev, empty_exp, []
        
        # الحصول على جميع أسماء الأوراق
        all_sheets = get_all_worksheets(conn)
        
        if not all_sheets:
            # محاولة قراءة كل الأوراق مرة واحدة
            try:
                all_data = conn.read(spreadsheet=SHEET_URL, worksheet=None)
                if all_data:
                    all_sheets = list(all_data.keys())
            except:
                pass
        
        st.sidebar.info(f"📄 الأوراق الموجودة في الجوجل شيت: {all_sheets if all_sheets else 'لا يمكن تحديدها'}")
        
        # محاولة العثور على أي ورقة تحتوي على بيانات الإيرادات
        revenue = empty_rev
        expenses = empty_exp
        
        if all_sheets:
            for sheet_name in all_sheets:
                try:
                    df = conn.read(worksheet=sheet_name, spreadsheet=SHEET_URL, ttl=0)
                    if df is not None and not df.empty:
                        # التحقق من أن هذه الورقة تحتوي على بيانات إيرادات (وجود عمود المالك أو الوحدة)
                        if any(col in str(df.columns) for col in ['مالك', 'وحدة', 'دور', 'شهر']):
                            if revenue.empty:
                                revenue = df
                                st.sidebar.success(f"✅ تم العثور على بيانات الإيرادات في ورقة: {sheet_name}")
                        # التحقق من وجود بيانات مصروفات
                        elif any(col in str(df.columns) for col in ['نوع', 'مبلغ', 'تاريخ']):
                            if expenses.empty:
                                expenses = df
                                st.sidebar.success(f"✅ تم العثور على بيانات المصروفات في ورقة: {sheet_name}")
                except:
                    continue
        
        # إذا لم نعثر على أي ورقة، نحاول قراءة أول ورقة
        if revenue.empty:
            try:
                first_sheet = all_sheets[0] if all_sheets else None
                if first_sheet:
                    revenue = conn.read(worksheet=first_sheet, spreadsheet=SHEET_URL, ttl=0)
                    st.sidebar.warning(f"⚠️ تم استخدام أول ورقة: {first_sheet}")
            except:
                pass
        
        return revenue, expenses, all_sheets
        
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
        return empty_rev, empty_exp, []

# تحميل البيانات
revenue, expenses, all_sheets = load_data()

# عرض أسماء الأوراق للمستخدم
if all_sheets:
    st.sidebar.markdown("---")
    st.sidebar.write("📋 **الأوراق الموجودة:**")
    for sheet in all_sheets:
        st.sidebar.write(f"- {sheet}")

# تنظيف البيانات
if not revenue.empty:
    # إعادة تسمية الأعمدة لتوحيدها
    column_mapping = {}
    for col in revenue.columns:
        col_str = str(col)
        if 'دور' in col_str:
            column_mapping[col] = 'الدور'
        elif 'وحدة' in col_str:
            column_mapping[col] = 'الوحدة'
        elif 'مالك' in col_str:
            column_mapping[col] = 'المالك'
        elif 'شهر' in col_str:
            column_mapping[col] = 'شهر الاستحقاق'
        elif 'اشتراك' in col_str or 'مطلوب' in col_str:
            column_mapping[col] = 'الاشتراك'
        elif 'مدفوع' in col_str or 'محصل' in col_str:
            column_mapping[col] = 'المدفوع'
        elif 'ملاحظات' in col_str:
            column_mapping[col] = 'ملاحظات'
    
    revenue = revenue.rename(columns=column_mapping)
    
    # تحويل الأعمدة الرقمية
    if 'الاشتراك' in revenue.columns:
        revenue['الاشتراك'] = pd.to_numeric(revenue['الاشتراك'], errors='coerce').fillna(0)
    else:
        revenue['الاشتراك'] = 0
        
    if 'المدفوع' in revenue.columns:
        revenue['المدفوع'] = pd.to_numeric(revenue['المدفوع'], errors='coerce').fillna(0)
    else:
        revenue['المدفوع'] = 0
        
    if 'شهر الاستحقاق' not in revenue.columns:
        revenue['شهر الاستحقاق'] = ""
    else:
        revenue['شهر الاستحقاق'] = revenue['شهر الاستحقاق'].astype(str).str.strip()
    
    if 'الدور' not in revenue.columns:
        revenue['الدور'] = ""
    if 'الوحدة' not in revenue.columns:
        revenue['الوحدة'] = ""
    if 'المالك' not in revenue.columns:
        revenue['المالك'] = ""
    if 'ملاحظات' not in revenue.columns:
        revenue['ملاحظات'] = ""

if not expenses.empty:
    for col in expenses.columns:
        col_str = str(col)
        if 'مبلغ' in col_str:
            expenses['المبلغ'] = pd.to_numeric(expenses[col], errors='coerce').fillna(0)
        elif 'تاريخ' in col_str:
            expenses['التاريخ'] = expenses[col]
        elif 'شهر' in col_str:
            expenses['الشهر'] = expenses[col]
        elif 'نوع' in col_str:
            expenses['النوع'] = expenses[col]
        elif 'تفاصيل' in col_str:
            expenses['التفاصيل'] = expenses[col]

def get_sorted_months(df, col):
    if df.empty or col not in df.columns:
        return []
    months = [str(m) for m in df[col].unique() if str(m).strip() and str(m).lower() != 'nan' and str(m) != '' and len(str(m)) > 4]
    return sorted(months, reverse=True)

# عرض حالة البيانات
if revenue.empty:
    st.warning("⚠️ لم يتم العثور على بيانات")
    st.info("""
    **الرجاء التأكد من:**
    
    1. تم مشاركة الجوجل شيت مع البريد: `phone-952@phoneproject.iam.gserviceaccount.com`
    2. في الجوجل شيت، اضغط على "مشاركة" وأضف هذا البريد بصلاحية "محرر"
    3. انتظر 2-3 دقائق بعد المشاركة
    4. ثم اضغط على زر "تحديث البيانات" في الشريط الجانبي
    
    **ملاحظة:** الكود الآن سيبحث تلقائياً عن أي ورقة تحتوي على بيانات، بغض النظر عن اسمها.
    """)
else:
    st.success(f"✅ تم تحميل {len(revenue)} سجل بنجاح!")
    
    # عرض معاينة للبيانات
    with st.sidebar.expander("📊 معاينة البيانات"):
        st.write(revenue.head(10))

menu = st.sidebar.radio("📋 القائمة الرئيسية", ["🏠 لوحة التحكم", "💰 الإيرادات", "💸 المصروفات", "⚠️ المتأخرات", "📊 التقارير"])

if menu == "🏠 لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات لعرضها")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("📅 عرض إحصائيات شهر:", all_m)
            
            df_r = revenue[revenue["شهر الاستحقاق"] == sel_m]
            
            t_sub = df_r["الاشتراك"].sum()
            t_paid = df_r["المدفوع"].sum()
            net = t_paid - t_sub
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 المطلوب", f"{int(t_sub):,} جنيه")
            col2.metric("✅ المحصل", f"{int(t_paid):,} جنيه")
            col3.metric("📈 صافي المتبقي", f"{int(net):,} جنيه")
            
            if not df_r.empty:
                st.subheader("📋 تفاصيل الإيرادات")
                df_r_display = df_r.copy()
                df_r_display["المتبقي"] = df_r_display["الاشتراك"] - df_r_display["المدفوع"]
                df_r_display["الحالة"] = df_r_display["المتبقي"].apply(lambda x: "🔴 متأخر" if x > 0 else "🟢 مدفوع")
                st.dataframe(df_r_display[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي", "الحالة", "ملاحظات"]], use_container_width=True)
        else:
            st.info("لا توجد شهور صالحة في البيانات")

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
        st.info("📭 لا توجد بيانات مصروفات. قم بإضافة ورقة للمصروفات في الجوجل شيت")
    else:
        st.dataframe(expenses, use_container_width=True)

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
            st.dataframe(late_display, use_container_width=True)
        else:
            st.success("🎉 لا توجد متأخرات!")

elif menu == "📊 التقارير":
    st.title("📊 التقارير المالية")
    
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("📅 اختر الشهر للتقرير:", all_m)
            df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
            
            if st.button("📄 توليد التقرير", use_container_width=True):
                total_required = df_r["الاشتراك"].sum()
                total_paid = df_r["المدفوع"].sum()
                net_profit = total_paid - total_required
                
                col1, col2, col3 = st.columns(3)
                col1.metric("المطلوب", f"{int(total_required):,} جنيه")
                col2.metric("المحصل", f"{int(total_paid):,} جنيه")
                col3.metric("المتبقي", f"{int(net_profit):,} جنيه")
                
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي"]], use_container_width=True)
        else:
            st.info("لا توجد شهور صالحة")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
