import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="نظام إدارة العمارة", layout="wide")

SHEET_ID = "1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw"
REVENUE_SHEET_NAME = "revenue"
EXPENSES_SHEET_NAME = "expenses"

REVENUE_URL = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pubhtml?gid=0&single=true"
EXPENSES_URL = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pubhtml?gid=627403180&single=true"

def ar(text):
    if pd.isna(text) or text == "": 
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

@st.cache_data(ttl=60)
def load_data():
    revenue_columns = ["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"]
    expenses_columns = ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"]
    empty_rev = pd.DataFrame(columns=revenue_columns)
    empty_exp = pd.DataFrame(columns=expenses_columns)
    try:
        try:
            revenue = pd.read_csv(REVENUE_URL)
            if revenue.empty or len(revenue.columns) < 3:
                revenue = empty_rev
            else:
                for col in revenue_columns:
                    if col not in revenue.columns:
                        revenue[col] = "" if col not in ["الاشتراك", "المدفوع"] else 0
        except:
            revenue = empty_rev
        try:
            expenses = pd.read_csv(EXPENSES_URL)
            if expenses.empty or len(expenses.columns) < 3:
                expenses = empty_exp
            else:
                for col in expenses_columns:
                    if col not in expenses.columns:
                        expenses[col] = "" if col != "المبلغ" else 0
        except:
            expenses = empty_exp
        return revenue, expenses
    except Exception as e:
        st.error(f"خطأ: {str(e)}")
        return empty_rev, empty_exp

revenue, expenses = load_data()

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

if revenue.empty:
    st.sidebar.warning("⚠️ لا توجد بيانات")
    with st.sidebar.expander("📖 طريقة ربط جوجل شيت", expanded=True):
        st.markdown(f"""
        **خطوات بسيطة:**
        1. افتح جوجل شيت: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
        2. انشئ ورقتين بالاسمين: {REVENUE_SHEET_NAME} و {EXPENSES_SHEET_NAME}
        3. في ورقة revenue اكتب: الدور | الوحدة | المالك | شهر الاستحقاق | الاشتراك | المدفوع | ملاحظات
        4. في ورقة expenses اكتب: التاريخ | الشهر | النوع | التفاصيل | المبلغ
        5. شارك الجوجل شيت مع "اي شخص لديه الرابط - مشاهد"
        6. اضغط على زر التحديث
        """)

menu = st.sidebar.radio("📋 القائمة الرئيسية", ["🏠 لوحة التحكم", "💰 الايرادات", "💸 المصروفات", "⚠️ المتاخرات", "📊 التقارير"])

if menu == "🏠 لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    if revenue.empty:
        st.info("📭 لا توجد بيانات")
        sample_rev = pd.DataFrame({
            "الدور": ["الاول", "الاول", "الثاني"],
            "الوحدة": ["101", "102", "201"],
            "المالك": ["احمد محمد", "سعيد علي", "محمد ابراهيم"],
            "شهر الاستحقاق": ["01/2025", "01/2025", "01/2025"],
            "الاشتراك": [500, 500, 500],
            "المدفوع": [500, 250, 0],
            "ملاحظات": ["", "باقي 250", "غير مدفوع"]
        })
        st.dataframe(sample_rev, use_container_width=True)
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("📅 عرض احصائيات شهر:", all_m)
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
            ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=2)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, f'{int(val):,}', ha='center', va='bottom', fontweight='bold', fontsize=12)
            ax.set_ylabel("القيمة (جنيه)", fontsize=12)
            ax.set_title(f"🏢 الملخص المالي لشهر {sel_m}", fontsize=16, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            with st.expander("📋 تفاصيل الايرادات"):
                df_r["الحالة"] = df_r.apply(lambda x: "🔴 متاخر" if x["الاشتراك"] - x["المدفوع"] > 0 else "🟢 مدفوع", axis=1)
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "الحالة", "ملاحظات"]], use_container_width=True)
            if not df_e.empty:
                with st.expander("💸 تفاصيل المصروفات"):
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
        else:
            st.info("لا توجد شهور مسجلة")

elif menu == "💰 الايرادات":
    st.title("💰 جدول الايرادات")
    if revenue.empty:
        st.warning("⚠️ لا توجد بيانات ايرادات")
        st.markdown(f"[📊 اضغط هنا لفتح جوجل شيت](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)")
    else:
        st.dataframe(revenue, use_container_width=True)
        st.subheader("📊 احصائيات سريعة")
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
        st.markdown(f"[📊 اضغط هنا لفتح جوجل شيت](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)")
    else:
        st.dataframe(expenses, use_container_width=True)
        total_exp = expenses['المبلغ'].sum()
        st.metric("اجمالي المصروفات", f"{int(total_exp):,} جنيه")
        if 'النوع' in expenses.columns:
            st.subheader("📊 المصروفات حسب النوع")
            exp_by_type = expenses.groupby('النوع')['المبلغ'].sum().sort_values(ascending=False)
            st.bar_chart(exp_by_type)

elif menu == "⚠️ المتاخرات":
    st.title("⚠️ كشف المتاخرات")
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
        late = revenue[revenue["المتبقي"] > 0].copy()
        if not late.empty:
            total_late = late["المتبقي"].sum()
            col1, col2 = st.columns(2)
            col1.metric("💰 اجمالي المتاخرات", f"{int(total_late):,} جنيه")
            col2.metric("📊 عدد الوحدات المتاخرة", f"{len(late)} وحدة")
            st.subheader("📋 قائمة المتاخرات")
            late_display = late[["المالك", "الوحدة", "الدور", "شهر الاستحقاق", "الاشتراك", "المدفوع", "المتبقي", "ملاحظات"]]
            late_display = late_display.sort_values("المتبقي", ascending=False)
            st.dataframe(late_display, use_container_width=True)
            csv = late_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label="📥 تحميل تقرير المتاخرات (CSV)", data=csv, file_name=f"متاخرات_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        else:
            st.success("🎉 لا توجد متاخرات! جميع الوحدات مسددة بالكامل.")
            st.balloons()

elif menu == "📊 التقارير":
    st.title("📊 التقارير المالية")
    if revenue.empty:
        st.info("لا توجد بيانات لعرض التقارير")
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
                st.subheader(f"📊 ملخص شهر {sel_m}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("المطلوب", f"{int(total_required):,} جنيه")
                col2.metric("المحصل", f"{int(total_paid):,} جنيه")
                col3.metric("المصاريف", f"{int(total_expenses):,} جنيه")
                col4.metric("صافي الربح", f"{int(net_profit):,} جنيه")
                st.progress(payment_rate / 100)
                st.caption(f"نسبة التحصيل: {payment_rate:.1f}%")
                st.subheader("📋 تفاصيل الايرادات")
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي"]], use_container_width=True)
                if not df_e.empty:
                    st.subheader("💸 تفاصيل المصروفات")
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
                fig, ax = plt.subplots(figsize=(8, 4))
                categories = ['المطلوب', 'المحصل', 'المصاريف']
                values = [total_required, total_paid, total_expenses]
                colors = ['#3498db', '#2ecc71', '#e74c3c']
                ax.bar(categories, values, color=colors, width=0.5)
                ax.set_ylabel('القيمة (جنيه)')
                ax.set_title(f'ملخص شهر {sel_m}')
                for i, v in enumerate(values):
                    ax.text(i, v + 10, str(int(v)), ha='center', fontweight='bold')
                st.pyplot(fig)
        else:
            st.info("لا توجد شهور مسجلة")

st.sidebar.markdown("---")
if not revenue.empty:
    total_unpaid = (revenue['الاشتراك'] - revenue['المدفوع']).sum() if 'الاشتراك' in revenue.columns else 0
    st.sidebar.info(f"📌 المعلومات\n- اليوم: {datetime.now().strftime('%Y-%m-%d')}\n- عدد الوحدات: {len(revenue['الوحدة'].unique()) if 'الوحدة' in revenue.columns else 0}\n- المتاخرات: {int(total_unpaid):,} جنيه")
if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.markdown(f"[📊 فتح جوجل شيت](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)")
