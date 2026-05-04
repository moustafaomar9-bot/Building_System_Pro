import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="نظام إدارة العمارة - الحساب التراكمي الفاخر", layout="wide")

# =====================================================
# دالة معالجة العربي للرسوم البيانية
# =====================================================
def ar(text):
    if pd.isna(text) or text == "": return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# =====================================================
# تحميل وحفظ البيانات
# =====================================================
file_path = "data.xlsx"

def load_data():
    if os.path.exists(file_path):
        try:
            rev = pd.read_excel(file_path, sheet_name="revenue")
            exp = pd.read_excel(file_path, sheet_name="expenses")
        except:
            rev = pd.DataFrame(columns=["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"])
            exp = pd.DataFrame(columns=["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])
    else:
        rev = pd.DataFrame(columns=["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"])
        exp = pd.DataFrame(columns=["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])

    rev["شهر الاستحقاق"] = rev["شهر الاستحقاق"].astype(str).replace(['nan', 'None'], '')
    rev["الاشتراك"] = pd.to_numeric(rev["الاشتراك"], errors="coerce").fillna(0)
    rev["المدفوع"] = pd.to_numeric(rev["المدفوع"], errors="coerce").fillna(0)

    if "الشهر" not in exp.columns: exp["الشهر"] = ""
    exp["الشهر"] = exp["الشهر"].astype(str).replace(['nan', 'None'], '')
    exp["المبلغ"] = pd.to_numeric(exp["المبلغ"], errors="coerce").fillna(0)

    return rev, exp

def save_all(rev_df, exp_df):
    with pd.ExcelWriter(file_path) as writer:
        rev_df.to_excel(writer, sheet_name="revenue", index=False)
        exp_df.to_excel(writer, sheet_name="expenses", index=False)

revenue, expenses = load_data()

def get_sorted_months(df, col):
    m_list = [str(m) for m in df[col].unique() if str(m).strip() != "" and str(m).lower() != 'nan']
    return sorted(m_list, reverse=True)

# =====================================================
# القائمة الجانبية
# =====================================================
menu = st.sidebar.radio("القائمة الرئيسية", ["لوحة التحكم", "الإيرادات", "المصاريف", "بدء شهر جديد", "المتأخرات", "التقارير الاحترافية"])

# =====================================================
# 1. لوحة التحكم
# =====================================================
if menu == "لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    all_m = get_sorted_months(revenue, "شهر الاستحقاق")
    if all_m:
        sel_m = st.selectbox("عرض إحصائيات شهر:", all_m)
        df_r = revenue[revenue["شهر الاستحقاق"] == sel_m]
        df_e = expenses[expenses["الشهر"] == sel_m]

        t_sub, t_paid = df_r["الاشتراك"].sum(), df_r["المدفوع"].sum()
        t_exp = df_e["المبلغ"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric(f"مطلوب {sel_m}", f"{int(t_sub):,}")
        c2.metric(f"محصل {sel_m}", f"{int(t_paid):,}")
        c3.metric(f"صافي الشهر", f"{int(t_paid - t_exp):,}")

        fig, ax = plt.subplots(figsize=(6, 2.5))
        ax.bar([ar("المطلوب"), ar("المحصل"), ar("المصاريف")], [t_sub, t_paid, t_exp], color=['#3498db', '#2ecc71', '#e74c3c'], width=0.5)
        st.pyplot(fig)
    else:
        st.info("لا توجد بيانات حالياً.")

# =====================================================
# 2. الإيرادات
# =====================================================
elif menu == "الإيرادات":
    st.subheader("📥 إدارة الإيرادات")
    all_m = get_sorted_months(revenue, "شهر الاستحقاق")
    if all_m:
        sel_m = st.selectbox("اختر الشهر للتعديل:", all_m)
        month_data = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
        edited_rev = st.data_editor(month_data, num_rows="dynamic", key="rev_ed")
        if st.button("حفظ التعديلات"):
            others = revenue[revenue["شهر الاستحقاق"] != sel_m]
            save_all(pd.concat([others, edited_rev], ignore_index=True), expenses)
            st.success("تم الحفظ بنجاح")
            st.rerun()

# =====================================================
# 3. المصاريف
# =====================================================
elif menu == "المصاريف":
    st.subheader("📤 إدارة المصروفات")
    all_m = get_sorted_months(revenue, "شهر الاستحقاق")
    te1, te2 = st.tabs(["💸 تسجيل مصروف", "📝 تعديل"])
    with te1:
        with st.form("exp_add"):
            col1, col2 = st.columns(2)
            e_date = col1.date_input("التاريخ", datetime.now())
            e_month = col2.selectbox("يسجل على شهر:", all_m if all_m else [datetime.now().strftime("%m/%Y")])
            e_type = st.selectbox("النوع", ["نظافة", "كهرباء", "مياه", "صيانة", "أخرى"])
            e_amt = st.number_input("المبلغ", 0)
            e_det = st.text_area("التفاصيل")
            if st.form_submit_button("حفظ"):
                new_exp = pd.DataFrame([[e_date.strftime("%Y-%m-%d"), e_month, e_type, e_det, e_amt]], columns=expenses.columns)
                save_all(revenue, pd.concat([expenses, new_exp], ignore_index=True))
                st.rerun()
    with te2:
        if all_m:
            sel_m_view = st.selectbox("عرض مصروفات شهر:", all_m)
            m_exp = expenses[expenses["الشهر"] == sel_m_view].copy()
            ed_exp = st.data_editor(m_exp, num_rows="dynamic")
            if st.button("حفظ التعديلات"):
                other_exp = expenses[expenses["الشهر"] != sel_m_view]
                save_all(revenue, pd.concat([other_exp, ed_exp], ignore_index=True))
                st.rerun()

# =====================================================
# 4. بدء شهر جديد (تعديل الحساب التراكمي التلقائي)
# =====================================================
elif menu == "بدء شهر جديد":
    st.title("🆕 ترحيل البيانات وحساب الأرصدة")
    all_m = get_sorted_months(revenue, "شهر الاستحقاق")
    if all_m:
        last_m = st.selectbox("نسخ البيانات من شهر:", all_m)
        new_m = st.text_input("الشهر الجديد (مثلاً 03/2026):")
        if st.button("تنفيذ الترحيل الآن"):
            if new_m in all_m: 
                st.error("الشهر موجود بالفعل!")
            else:
                last_data = revenue[revenue["شهر الاستحقاق"] == last_m].copy()
                new_rows = []
                for _, r in last_data.iterrows():
                    # الحساب التراكمي الذكي
                    diff = r["الاشتراك"] - r["المدفوع"]

                    if diff > 0: # مديونية
                        note = f"متأخرات سابقة: {int(diff)}"
                        paid_in_new = 0
                    elif diff < 0: # فائض (دفع أكثر)
                        surplus = abs(diff)
                        note = f"خصم فائض سابق: {int(surplus)}"
                        paid_in_new = surplus # ترحيل الفائض لخانة المدفوع تلقائياً
                    else: # دفع بالضبط
                        note = "خالص"
                        paid_in_new = 0

                    new_rows.append([r["الدور"], r["الوحدة"], r["المالك"], new_m, r["الاشتراك"], paid_in_new, note])

                save_all(pd.concat([revenue, pd.DataFrame(new_rows, columns=revenue.columns)], ignore_index=True), expenses)
                st.success(f"✅ تم ترحيل {len(new_rows)} وحدة بنجاح مع معالجة الفوائض والمتأخرات.")
                st.balloons()
    else:
        st.info("لا توجد بيانات للترحيل. أضف شهراً يدوياً أولاً.")

# =====================================================
# 5. المتأخرات
# =====================================================
elif menu == "المتأخرات":
    st.subheader("⚠️ كشف المتأخرات")
    revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
    late = revenue[revenue["المتبقي"] > 0].copy()
    if not late.empty:
        st.dataframe(late[["المالك", "الوحدة", "شهر الاستحقاق", "المتبقي", "ملاحظات"]])
    else: st.success("🎉 لا توجد متأخرات!")

# =====================================================
# 6. التقارير الاحترافية (التنسيق الفاخر المطلوب)
# =====================================================
elif menu == "التقارير الاحترافية":
    st.title("📑 التقارير المالية الاحترافية")
    all_m = get_sorted_months(revenue, "شهر الاستحقاق")
    if all_m:
        sel_m = st.selectbox("اختر الشهر للتقرير", all_m)

        if st.button("توليد التقرير الفاخر"):
            df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
            df_e = expenses[expenses["الشهر"] == sel_m].copy()

            def get_h(row):
                d = row['الاشتراك'] - row['المدفوع']
                if d > 0: return f'<span style="color:red; font-weight:bold;">مطلوب: {int(d):,}</span>'
                elif d < 0: return f'<span style="color:green; font-weight:bold;">له رصيد: {int(abs(d)):,}</span>'
                return '<span style="color:gray;">مسدد</span>'

            df_r["حالة الحساب"] = df_r.apply(get_h, axis=1)
            s_t, p_t = df_r["الاشتراك"].sum(), df_r["المدفوع"].sum()
            e_t = df_e["المبلغ"].sum()

            full_html = f"""
            <!DOCTYPE html>
            <html lang="ar">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ direction: rtl; font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; background-color: #f0f2f5; }}
                    .report-card {{ background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 1000px; margin: auto; }}
                    .header-title {{ color: #1a2a6c; text-align: center; font-size: 32px; font-weight: bold; margin-bottom: 10px; border-bottom: 5px solid #3498db; padding-bottom: 15px; }}
                    .stat-box {{ display: flex; gap: 15px; margin: 30px 0; }}
                    .card {{ flex: 1; padding: 20px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                    .blue {{ background: linear-gradient(135deg, #1e3c72, #2a5298); }}
                    .green {{ background: linear-gradient(135deg, #11998e, #38ef7d); }}
                    .red {{ background: linear-gradient(135deg, #cb2d3e, #ef473a); }}
                    .dark {{ background: linear-gradient(135deg, #232526, #414345); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 25px; background: white; border-radius: 10px; overflow: hidden; }}
                    th {{ background-color: #1a2a6c; color: white; padding: 15px; text-align: center; }}
                    td {{ padding: 12px; border: 1px solid #eee; text-align: center; font-size: 14px; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <div class="report-card">
                    <div class="header-title">التقرير المالي لشهر {sel_m}</div>
                    <div class="stat-box">
                        <div class="card blue"><h3>المطلوب</h3><p>{int(s_t):,}</p></div>
                        <div class="card green"><h3>المحصل</h3><p>{int(p_t):,}</p></div>
                        <div class="card red"><h3>المصاريف</h3><p>{int(e_t):,}</p></div>
                        <div class="card dark"><h3>صافي الرصيد</h3><p>{int(p_t - e_t):,}</p></div>
                    </div>
                    <h3 style="color: #1a2a6c; border-right: 5px solid #3498db; padding-right: 10px;">📋 كشف اشتراكات الوحدات</h3>
                    {df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "حالة الحساب"]].to_html(index=False, escape=False)}
                    <h3 style="margin-top:40px; color: #1a2a6c; border-right: 5px solid #e74c3c; padding-right: 10px;">💸 كشف المصروفات التفصيلي</h3>
                    {df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]].to_html(index=False)}
                </div>
            </body>
            </html>
            """
            st.components.v1.html(full_html, height=700, scrolling=True)
            st.download_button(f"💾 تحميل تقرير شهر {sel_m}", full_html, f"Report_{sel_m}.html", "text/html")
    else: st.info("لا توجد شهور مسجلة.")
