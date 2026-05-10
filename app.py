import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="نظام إدارة العمارة - الحساب التراكمي الفاخر", layout="wide")

# =====================================================
# روابط CSV من جوجل شيت (بعد النشر على الويب)
# =====================================================
# ⚠️ ضع هنا الروابط التي نسختها من خطوة النشر ⚠️
# اذهب إلى ملف ← نشر على الويب ← اختر الورقة ← CSV ← انسخ الرابط
REVENUE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pub?gid=0&single=true&output=csv"
EXPENSES_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pub?gid=627403180&single=true&output=csv"

# =====================================================
# دالة معالجة العربي للرسوم البيانية
# =====================================================
def ar(text):
    if pd.isna(text) or text == "": return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# =====================================================
# تحميل البيانات من جوجل شيت
# =====================================================
@st.cache_data(ttl=60)
def load_revenue():
    """تحميل بيانات الإيرادات من جوجل شيت"""
    try:
        df = pd.read_csv(REVENUE_CSV_URL)
        
        # إعادة تسمية الأعمدة إذا لزم الأمر (عدل حسب أسماء الأعمدة في ملفك)
        # إذا كانت الأعمدة بأسماء مختلفة، غيرها هنا
        # مثال: df = df.rename(columns={'إسم العمود القديم': 'الاسم الجديد'})
        
        # التأكد من وجود الأعمدة المطلوبة
        required_cols = ["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" if col not in ["الاشتراك", "المدفوع"] else 0
        
        # تحويل الأعمدة الرقمية
        df["الاشتراك"] = pd.to_numeric(df["الاشتراك"], errors="coerce").fillna(0)
        df["المدفوع"] = pd.to_numeric(df["المدفوع"], errors="coerce").fillna(0)
        df["شهر الاستحقاق"] = df["شهر الاستحقاق"].astype(str).replace(['nan', 'None', '<NA>', ''], '')
        
        return df
    except Exception as e:
        st.warning(f"لا يمكن تحميل الإيرادات: {str(e)[:100]}")
        return pd.DataFrame(columns=["الدور", "الوحدة", "المالك", "شهر الاستحقاق", "الاشتراك", "المدفوع", "ملاحظات"])

@st.cache_data(ttl=60)
def load_expenses():
    """تحميل بيانات المصروفات من جوجل شيت"""
    try:
        df = pd.read_csv(EXPENSES_CSV_URL)
        
        # التأكد من وجود الأعمدة المطلوبة
        required_cols = ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" if col != "المبلغ" else 0
        
        df["المبلغ"] = pd.to_numeric(df["المبلغ"], errors="coerce").fillna(0)
        df["الشهر"] = df["الشهر"].astype(str).replace(['nan', 'None', '<NA>', ''], '')
        
        return df
    except Exception as e:
        st.warning(f"لا يمكن تحميل المصروفات: {str(e)[:100]}")
        return pd.DataFrame(columns=["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])

# تحميل البيانات
revenue = load_revenue()
expenses = load_expenses()

def get_sorted_months(df, col):
    m_list = [str(m) for m in df[col].unique() if str(m).strip() != "" and str(m).lower() != 'nan']
    return sorted(m_list, reverse=True)

# =====================================================
# تنبيه للمستخدم إذا لم توجد بيانات
# =====================================================
if revenue.empty:
    st.sidebar.warning("⚠️ لا توجد بيانات")
    with st.sidebar.expander("📖 طريقة ربط جوجل شيت", expanded=True):
        st.markdown("""
        ### خطوات ربط جوجل شيت:
        
        1. **افتح جوجل شيت** من الرابط
        
        2. **اذهب إلى: ملف ← مشاركة ← نشر على الويب**
        
        3. **اختر الورقة التي فيها البيانات** (revenue)
        
        4. **اختر CSV** من القائمة المنسدلة
        
        5. **اضغط على نشر**
        
        6. **انسخ الرابط** وضعه في المتغير `REVENUE_CSV_URL`
        
        7. **كرر الخطوات 3-6** لورقة المصروفات (expenses)
        
        8. **اضغط على زر التحديث** 👇
        """)

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
        t_exp = df_e["المبلغ"].sum() if not df_e.empty else 0

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
# 2. الإيرادات (عرض فقط - للتعديل عدل في جوجل شيت)
# =====================================================
elif menu == "الإيرادات":
    st.subheader("📥 الإيرادات")
    if revenue.empty:
        st.warning("لا توجد بيانات إيرادات")
    else:
        st.dataframe(revenue, use_container_width=True)
        st.info("📌 للتعديل: افتح جوجل شيت مباشرة وقم بتعديل البيانات، ثم اضغط تحديث البيانات")

# =====================================================
# 3. المصاريف (عرض فقط - للتعديل عدل في جوجل شيت)
# =====================================================
elif menu == "المصاريف":
    st.subheader("📤 المصروفات")
    
    if expenses.empty:
        st.warning("لا توجد بيانات مصروفات")
        st.info("لإضافة مصروفات: قم بإضافة ورقة expenses في جوجل شيت بالأعمدة: التاريخ, الشهر, النوع, التفاصيل, المبلغ")
    else:
        st.dataframe(expenses, use_container_width=True)
        
        # عرض المصروفات حسب النوع
        if 'النوع' in expenses.columns:
            st.subheader("📊 المصروفات حسب النوع")
            exp_by_type = expenses.groupby('النوع')['المبلغ'].sum().sort_values(ascending=False)
            st.bar_chart(exp_by_type)
        
        st.info("📌 للتعديل: افتح جوجل شيت مباشرة وقم بتعديل البيانات، ثم اضغط تحديث البيانات")

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

                # عرض البيانات الجديدة
                new_month_data = pd.DataFrame(new_rows, columns=revenue.columns)
                st.success(f"✅ تم إنشاء {len(new_rows)} سجل لشهر {new_m}")
                st.dataframe(new_month_data, use_container_width=True)
                st.info("📌 ملاحظة: هذه بيانات معروضة فقط. لإضافتها بشكل دائم، قم بنسخها إلى ورقة revenue في جوجل شيت")
                st.balloons()
    else:
        st.info("لا توجد بيانات للترحيل. أضف شهراً يدوياً أولاً.")

# =====================================================
# 5. المتأخرات
# =====================================================
elif menu == "المتأخرات":
    st.subheader("⚠️ كشف المتأخرات")
    if revenue.empty:
        st.info("لا توجد بيانات")
    else:
        revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
        late = revenue[revenue["المتبقي"] > 0].copy()
        if not late.empty:
            total_late = late["المتبقي"].sum()
            st.metric("💰 إجمالي المتأخرات", f"{int(total_late):,} جنيه")
            st.dataframe(late[["المالك", "الوحدة", "شهر الاستحقاق", "المتبقي", "ملاحظات"]], use_container_width=True)
        else: 
            st.success("🎉 لا توجد متأخرات!")

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
            e_t = df_e["المبلغ"].sum() if not df_e.empty else 0

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
                    {df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]].to_html(index=False) if not df_e.empty else "<p>لا توجد مصروفات</p>"}
                </div>
            </body>
            </html>
            """
            st.components.v1.html(full_html, height=700, scrolling=True)
            st.download_button(f"💾 تحميل تقرير شهر {sel_m}", full_html, f"Report_{sel_m}.html", "text/html")
    else: 
        st.info("لا توجد شهور مسجلة.")

# =====================================================
# الشريط الجانبي - أزرار التحديث والمعلومات
# =====================================================
st.sidebar.markdown("---")

if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# رابط سريع لجوجل شيت
st.sidebar.markdown(f"[📊 فتح جوجل شيت](https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw/edit)")

# عرض معلومات
if not revenue.empty:
    total_unpaid = (revenue['الاشتراك'] - revenue['المدفوع']).sum()
