import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from streamlit_gsheets import GSheetsConnection

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام إدارة العمارة - النسخة الفاخرة", layout="wide")

# 2. معالجة المفتاح السري
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# دالة معالجة العربي
def ar(text):
    if pd.isna(text) or text == "": 
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# الدالة المفقودة لحفظ البيانات
def save_all(revenue_df, expenses_df):
    """حفظ البيانات إلى جوجل شيت"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # حفظ الإيرادات
        conn.update(worksheet="revenue", data=revenue_df)
        
        # حفظ المصروفات
        conn.update(worksheet="expenses", data=expenses_df)
        
        st.success("✅ تم حفظ البيانات بنجاح في جوجل شيت!")
        return True
    except Exception as e:
        st.error(f"❌ خطأ في الحفظ: {str(e)[:200]}")
        return False

# الاتصال وتحميل البيانات
@st.cache_data(ttl=60)
def load_data():
    """تحميل البيانات من جوجل شيت"""
    # تعريف هيكل البيانات الافتراضي
    revenue_columns = ["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"]
    expenses_columns = ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"]
    
    empty_rev = pd.DataFrame(columns=revenue_columns)
    empty_exp = pd.DataFrame(columns=expenses_columns)
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # محاولة قراءة البيانات من الأوراق المحددة
        rev = conn.read(worksheet="revenue", ttl=0)
        exp = conn.read(worksheet="expenses", ttl=0)
        
        # التحقق من وجود بيانات
        if rev.empty:
            rev = empty_rev
        else:
            # التأكد من وجود جميع الأعمدة المطلوبة
            for col in revenue_columns:
                if col not in rev.columns:
                    rev[col] = "" if col not in ["الاشتراك", "المدفوع"] else 0
        
        if exp.empty:
            exp = empty_exp
        else:
            for col in expenses_columns:
                if col not in exp.columns:
                    exp[col] = "" if col != "المبلغ" else 0
        
        return rev, exp
        
    except Exception as e:
        st.warning(f"⚠️ لا يمكن الاتصال بجوجل شيت: {str(e)[:150]}")
        return empty_rev, empty_exp

# تحميل البيانات
revenue, expenses = load_data()

# تنظيف البيانات بعد التحميل
if not revenue.empty:
    revenue["شهر الاستحقاق"] = revenue["شهر الاستحقاق"].astype(str).replace(['nan', 'None', '<NA>', ''], '')
    revenue["الاشتراك"] = pd.to_numeric(revenue["الاشتراك"], errors="coerce").fillna(0)
    revenue["المدفوع"] = pd.to_numeric(revenue["المدفوع"], errors="coerce").fillna(0)
    
if not expenses.empty:
    if "الشهر" not in expenses.columns:
        expenses["الشهر"] = ""
    expenses["الشهر"] = expenses["الشهر"].astype(str).replace(['nan', 'None', '<NA>', ''], '')
    expenses["المبلغ"] = pd.to_numeric(expenses["المبلغ"], errors="coerce").fillna(0)

# دالة ترتيب الشهور
def get_sorted_months(df, col):
    if df.empty or col not in df.columns:
        return []
    months = [str(m) for m in df[col].unique() if str(m).strip() and str(m).lower() != 'nan' and str(m) != '']
    months = [m for m in months if m and m != '']
    return sorted(months, reverse=True)

# عرض رسالة إذا لم تكن هناك بيانات
if revenue.empty and expenses.empty:
    st.warning("لا توجد بيانات لعرضها. يرجى مشاركة الجوجل شيت مع حساب الخدمة.")
    
    with st.expander("🔧 كيفية حل مشكلة الاتصال بجوجل شيت"):
        st.markdown("""
        **خطوات حل المشكلة:**
        
        1. افتح رابط الجوجل شيت
        2. اضغط على زر مشاركة (Share) في أعلى اليمين
        3. أضف هذا البريد الإلكتروني: phone-952@phoneproproject.iam.gserviceaccount.com
        4. اختر صلاحية محرر (Editor)
        5. اضغط على إرسال (Send)
        6. انتظر 2-3 دقائق ثم حدث الصفحة
        """)

# =====================================================
# القائمة الجانبية
# =====================================================
menu = st.sidebar.radio(
    "القائمة الرئيسية",
    ["لوحة التحكم", "الإيرادات", "المصاريف", "بدء شهر جديد", "المتأخرات", "التقارير الاحترافية"]
)

# =====================================================
# 1. لوحة التحكم
# =====================================================
if menu == "لوحة التحكم":
    st.title("ملخص المركز المالي")
    
    if revenue.empty:
        st.info("لا توجد بيانات ايرادات لعرضها")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("عرض احصائيات شهر:", all_m)
            
            df_r = revenue[revenue["شهر الاستحقاق"] == sel_m]
            df_e = expenses[expenses["الشهر"] == sel_m] if not expenses.empty else pd.DataFrame()
            
            t_sub = df_r["الاشتراك"].sum()
            t_paid = df_r["المدفوع"].sum()
            t_exp = df_e["المبلغ"].sum() if not df_e.empty else 0
            net = t_paid - t_exp
            
            # عرض المؤشرات
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("المطلوب", f"{int(t_sub):,} جنيه")
            c2.metric("المحصل", f"{int(t_paid):,} جنيه")
            c3.metric("المصاريف", f"{int(t_exp):,} جنيه")
            c4.metric("صافي الربح", f"{int(net):,} جنيه")
            
            # الرسم البياني
            fig, ax = plt.subplots(figsize=(10, 5))
            categories = [ar("المطلوب"), ar("المحصل"), ar("المصاريف")]
            values = [t_sub, t_paid, t_exp]
            colors = ['#3498db', '#2ecc71', '#e74c3c']
            ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=1)
            ax.set_ylabel("القيمة (جنيه)", fontsize=12)
            ax.set_title(f"الملخص المالي لشهر {sel_m}", fontsize=16, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
        else:
            st.info("لا توجد شهور مسجلة")

# =====================================================
# 2. الإيرادات
# =====================================================
elif menu == "الإيرادات":
    st.title("إدارة الايرادات")
    
    if revenue.empty:
        st.warning("لا توجد بيانات ايرادات")
        
        if st.button("انشاء نموذج مبدئي للايرادات"):
            sample_data = pd.DataFrame({
                "الدور": ["الاول", "الاول", "الثاني"],
                "الوحدة": ["101", "102", "201"],
                "المالك": ["احمد محمد", "سعيد علي", "محمد ابراهيم"],
                "شهر الاستحقاق": [datetime.now().strftime("%m/%Y"), datetime.now().strftime("%m/%Y"), datetime.now().strftime("%m/%Y")],
                "الاشتراك": [500, 500, 500],
                "المدفوع": [0, 0, 0],
                "ملاحظات": ["", "", ""]
            })
            save_all(sample_data, expenses)
            st.rerun()
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("اختر الشهر للتعديل:", all_m)
            month_data = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
            
            st.subheader(f"تعديل بيانات شهر {sel_m}")
            edited_rev = st.data_editor(month_data, num_rows="dynamic", use_container_width=True, key="rev_ed")
            
            if st.button("حفظ التعديلات", use_container_width=True):
                others = revenue[revenue["شهر الاستحقاق"] != sel_m]
                save_all(pd.concat([others, edited_rev], ignore_index=True), expenses)
                st.rerun()

# =====================================================
# 3. المصاريف
# =====================================================
elif menu == "المصاريف":
    st.title("إدارة المصروفات")
    
    all_m = get_sorted_months(revenue, "شهر الاستحقاق") if not revenue.empty else []
    
    tab1, tab2 = st.tabs(["تسجيل مصروف جديد", "تعديل المصروفات"])
    
    with tab1:
        with st.form("exp_add_form", clear_on_submit=True):
            st.subheader("تسجيل مصروف جديد")
            col1, col2 = st.columns(2)
            
            with col1:
                e_date = st.date_input("التاريخ", datetime.now())
                e_type = st.selectbox("نوع المصروف", ["نظافة", "كهرباء", "مياه", "غاز", "صيانة", "اجور", "اخرى"])
                e_amt = st.number_input("المبلغ (جنيه)", min_value=0, step=10, value=0)
            
            with col2:
                if all_m:
                    e_month = st.selectbox("يسجل على شهر:", all_m)
                else:
                    e_month = st.text_input("الشهر", datetime.now().strftime("%m/%Y"))
                e_det = st.text_area("التفاصيل")
            
            submitted = st.form_submit_button("حفظ المصروف", use_container_width=True)
            
            if submitted and e_amt > 0:
                new_exp = pd.DataFrame([[
                    e_date.strftime("%Y-%m-%d"), e_month, e_type, e_det, e_amt
                ]], columns=expenses.columns if not expenses.empty else ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])
                
                if save_all(revenue, pd.concat([expenses, new_exp], ignore_index=True)):
                    st.success("تم تسجيل المصروف بنجاح!")
                    st.rerun()
    
    with tab2:
        if not expenses.empty and all_m:
            sel_m_view = st.selectbox("عرض مصروفات شهر:", all_m, key="exp_view")
            m_exp = expenses[expenses["الشهر"] == sel_m_view].copy()
            
            if not m_exp.empty:
                ed_exp = st.data_editor(m_exp, num_rows="dynamic", use_container_width=True, key="exp_ed")
                
                if st.button("حفظ التعديلات", use_container_width=True, key="save_exp"):
                    other_exp = expenses[expenses["الشهر"] != sel_m_view]
                    save_all(revenue, pd.concat([other_exp, ed_exp], ignore_index=True))
                    st.rerun()

# =====================================================
# 4. بدء شهر جديد
# =====================================================
elif menu == "بدء شهر جديد":
    st.title("ترحيل البيانات لشهر جديد")
    
    if revenue.empty:
        st.warning("لا توجد بيانات سابقة للترحيل")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            col1, col2 = st.columns(2)
            
            with col1:
                last_m = st.selectbox("نسخ البيانات من شهر:", all_m)
            
            with col2:
                default_new = datetime.now().strftime("%m/%Y")
                new_m = st.text_input("الشهر الجديد:", default_new)
            
            if st.button("تنفيذ الترحيل", use_container_width=True):
                if new_m in all_m:
                    st.error(f"الشهر {new_m} موجود بالفعل")
                elif new_m:
                    last_data = revenue[revenue["شهر الاستحقاق"] == last_m].copy()
                    new_rows = []
                    
                    for _, row in last_data.iterrows():
                        debt = row["الاشتراك"] - row["المدفوع"]
                        note = f"متاخرات من {last_m}: {int(debt)}" if debt > 0 else "مسدد"
                        
                        new_rows.append([
                            row["الدور"], row["الوحدة"], row["المالك"], 
                            new_m, row["الاشتراك"], 0, note
                        ])
                    
                    new_month_data = pd.DataFrame(new_rows, columns=revenue.columns)
                    updated_revenue = pd.concat([revenue, new_month_data], ignore_index=True)
                    
                    if save_all(updated_revenue, expenses):
                        st.balloons()
                        st.success(f"تم ترحيل البيانات الى شهر {new_m}")
                        st.rerun()

# =====================================================
# 5. المتأخرات
# =====================================================
elif menu == "المتأخرات":
    st.title("كشف المتاخرات")
    
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
        late = revenue[revenue["المتبقي"] > 0].copy()
        
        if not late.empty:
            total_late = late["المتبقي"].sum()
            st.metric("اجمالي المتاخرات", f"{int(total_late):,} جنيه")
            
            late_display = late[["المالك", "الوحدة", "الدور", "شهر الاستحقاق", "الاشتراك", "المدفوع", "المتبقي"]]
            st.dataframe(late_display, use_container_width=True)
        else:
            st.success("لا توجد متاخرات")

# =====================================================
# 6. التقارير الاحترافية
# =====================================================
elif menu == "التقارير الاحترافية":
    st.title("التقارير المالية")
    
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("اختر الشهر للتقرير:", all_m)
            
            if st.button("توليد التقرير", use_container_width=True):
                df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
                df_e = expenses[expenses["الشهر"] == sel_m].copy() if not expenses.empty else pd.DataFrame()
                
                # حساب الاجماليات
                total_required = df_r["الاشتراك"].sum()
                total_paid = df_r["المدفوع"].sum()
                total_expenses = df_e["المبلغ"].sum() if not df_e.empty else 0
                net_profit = total_paid - total_expenses
                
                # عرض الملخص
                st.subheader("ملخص الشهر")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("المطلوب", f"{int(total_required):,}")
                col2.metric("المحصل", f"{int(total_paid):,}")
                col3.metric("المصاريف", f"{int(total_expenses):,}")
                col4.metric("صافي الربح", f"{int(net_profit):,}")
                
                # عرض الجداول
                st.subheader("تفاصيل الايرادات")
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع"]], use_container_width=True)
                
                if not df_e.empty:
                    st.subheader("تفاصيل المصروفات")
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)

# معلومات في الشريط الجانبي
st.sidebar.markdown("---")
st.sidebar.info(f"""
**معلومات النظام**
- تاريخ اليوم: {datetime.now().strftime("%Y-%m-%d")}
- عدد الوحدات: {len(revenue["الوحدة"].unique()) if not revenue.empty else 0}
""")

if st.sidebar.button("تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
