import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد الصفحة
st.set_page_config(page_title="نظام إدارة العمارة - النسخة الكاملة", layout="wide")

# دالة معالجة العربي
def ar(text):
    if pd.isna(text) or text == "": 
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# =====================================================
# روابط CSV من جوجل شيت (بعد النشر على الويب)
# =====================================================
# ⚠️ ضع هنا الروابط التي نسختها من خطوة النشر ⚠️
REVENUE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pub?output=csv"
EXPENSES_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pub?gid=627403180&single=true&output=csv"

# =====================================================
# تحميل البيانات
# =====================================================
@st.cache_data(ttl=60)
def load_revenue():
    """تحميل بيانات الإيرادات من جوجل شيت"""
    try:
        df = pd.read_csv(REVENUE_CSV_URL)
        
        # إعادة تسمية الأعمدة إذا لزم الأمر
        # تأكد من تطابق أسماء الأعمدة مع ما هو موجود في ملفك
        expected_cols = ['الدور', 'الوحدة', 'المالك', 'شهر الاستحقاق', 'الاشتراك', 'المدفوع', 'ملاحظات']
        
        # تحويل الأعمدة الرقمية
        if 'الاشتراك' in df.columns:
            df['الاشتراك'] = pd.to_numeric(df['الاشتراك'], errors='coerce').fillna(0)
        else:
            df['الاشتراك'] = 0
            
        if 'المدفوع' in df.columns:
            df['المدفوع'] = pd.to_numeric(df['المدفوع'], errors='coerce').fillna(0)
        else:
            df['المدفوع'] = 0
        
        # تنظيف الشهور
        if 'شهر الاستحقاق' in df.columns:
            df['شهر الاستحقاق'] = df['شهر الاستحقاق'].astype(str).str.strip()
        else:
            df['شهر الاستحقاق'] = ""
        
        # التأكد من وجود باقي الأعمدة
        if 'ملاحظات' not in df.columns:
            df['ملاحظات'] = ""
        if 'الدور' not in df.columns:
            df['الدور'] = ""
        if 'الوحدة' not in df.columns:
            df['الوحدة'] = ""
        if 'المالك' not in df.columns:
            df['المالك'] = ""
        
        st.success(f"✅ تم تحميل {len(df)} سجل إيرادات")
        return df
        
    except Exception as e:
        st.warning(f"لا يمكن تحميل الإيرادات: {str(e)[:100]}")
        return pd.DataFrame(columns=['الدور', 'الوحدة', 'المالك', 'شهر الاستحقاق', 'الاشتراك', 'المدفوع', 'ملاحظات'])

@st.cache_data(ttl=60)
def load_expenses():
    """تحميل بيانات المصروفات من جوجل شيت"""
    try:
        df = pd.read_csv(EXPENSES_CSV_URL)
        
        # تحويل الأعمدة الرقمية
        if 'المبلغ' in df.columns:
            df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0)
        else:
            df['المبلغ'] = 0
        
        # التأكد من وجود الأعمدة المطلوبة
        expected_cols = ['التاريخ', 'الشهر', 'النوع', 'التفاصيل', 'المبلغ']
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        
        if 'الشهر' in df.columns:
            df['الشهر'] = df['الشهر'].astype(str).str.strip()
        
        st.success(f"✅ تم تحميل {len(df)} سجل مصروفات")
        return df
        
    except Exception as e:
        st.warning(f"لا يمكن تحميل المصروفات: {str(e)[:100]}")
        return pd.DataFrame(columns=['التاريخ', 'الشهر', 'النوع', 'التفاصيل', 'المبلغ'])

# تحميل البيانات
revenue = load_revenue()
expenses = load_expenses()

# دالة ترتيب الشهور
def get_sorted_months(df, col):
    if df.empty or col not in df.columns:
        return []
    months = [str(m) for m in df[col].unique() if str(m).strip() and str(m).lower() != 'nan' and str(m) != '' and str(m) != '0']
    months = [m for m in months if m and m != '' and len(m) >= 5]
    return sorted(months, reverse=True)

# =====================================================
# القائمة الجانبية
# =====================================================
menu = st.sidebar.radio(
    "📋 القائمة الرئيسية",
    ["🏠 لوحة التحكم", "💰 الإيرادات", "💸 المصروفات", "🆕 بدء شهر جديد", "⚠️ المتأخرات", "📊 التقارير الاحترافية"]
)

# =====================================================
# 1. لوحة التحكم
# =====================================================
if menu == "🏠 لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات إيرادات")
        st.markdown("""
        ### لإضافة البيانات:
        1. افتح جوجل شيت وأضف البيانات في ورقة الإيرادات
        2. اذهب إلى ملف ← نشر على الويب ← CSV ← نشر
        3. انسخ الرابط وضعه في المتغير REVENUE_CSV_URL
        4. اضغط على زر التحديث
        """)
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
            
            # الرسم البياني
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
            
            # تفاصيل الإيرادات
            with st.expander("📋 تفاصيل الإيرادات", expanded=True):
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                df_r["الحالة"] = df_r["المتبقي"].apply(lambda x: "🔴 متأخر" if x > 0 else "🟢 مدفوع")
                st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي", "الحالة", "ملاحظات"]], use_container_width=True)
            
            # تفاصيل المصروفات
            if not df_e.empty:
                with st.expander("💸 تفاصيل المصروفات"):
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
        else:
            st.info("لا توجد شهور مسجلة في البيانات")

# =====================================================
# 2. الإيرادات
# =====================================================
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
        col3.metric("المتبقي", f"{int(total_required - total_paid):,} جنيه", 
                   delta="متأخرات" if total_required - total_paid > 0 else "مدفوع بالكامل")

# =====================================================
# 3. المصاريف
# =====================================================
elif menu == "💸 المصروفات":
    st.title("💸 جدول المصروفات")
    
    if expenses.empty:
        st.warning("⚠️ لا توجد بيانات مصروفات")
        st.info("لإضافة مصروفات، قم بإنشاء ورقة جديدة في جوجل شيت باسم 'expenses' ثم انشرها على الويب")
    else:
        st.dataframe(expenses, use_container_width=True)
        total_exp = expenses['المبلغ'].sum()
        st.metric("اجمالي المصروفات", f"{int(total_exp):,} جنيه")
        
        if 'النوع' in expenses.columns:
            st.subheader("📊 المصروفات حسب النوع")
            exp_by_type = expenses.groupby('النوع')['المبلغ'].sum().sort_values(ascending=False)
            st.bar_chart(exp_by_type)
            st.dataframe(exp_by_type.reset_index().rename(columns={'النوع': 'نوع المصروف', 'المبلغ': 'الإجمالي'}), use_container_width=True)

# =====================================================
# 4. بدء شهر جديد
# =====================================================
elif menu == "🆕 بدء شهر جديد":
    st.title("🆕 ترحيل البيانات لشهر جديد")
    
    if revenue.empty:
        st.warning("⚠️ لا توجد بيانات سابقة للترحيل")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            col1, col2 = st.columns(2)
            with col1:
                last_m = st.selectbox("📋 نسخ البيانات من شهر:", all_m)
            with col2:
                default_new = datetime.now().strftime("%m/%Y")
                new_m = st.text_input("📅 الشهر الجديد (مثال: 04/2026):", default_new)
            
            st.info(f"ℹ️ سيتم نسخ جميع الوحدات من شهر {last_m} إلى شهر {new_m} مع إعادة تعيين المدفوعات إلى صفر")
            
            if st.button("🚀 تنفيذ الترحيل", use_container_width=True):
                if new_m in all_m:
                    st.error(f"❌ الشهر {new_m} موجود بالفعل!")
                elif not new_m:
                    st.warning("⚠️ برجاء كتابة اسم الشهر الجديد")
                else:
                    last_data = revenue[revenue["شهر الاستحقاق"] == last_m].copy()
                    new_rows = []
                    for _, row in last_data.iterrows():
                        debt = row["الاشتراك"] - row["المدفوع"]
                        note = f"متأخرات من {last_m}: {int(debt)} جنيه" if debt > 0 else "مسدد بالكامل"
                        new_rows.append([row["الدور"], row["الوحدة"], row["المالك"], new_m, row["الاشتراك"], 0, note])
                    
                    new_month_data = pd.DataFrame(new_rows, columns=revenue.columns)
                    st.success(f"✅ تم إنشاء {len(new_rows)} سجل لشهر {new_m}")
                    st.dataframe(new_month_data, use_container_width=True)
                    st.info("📌 ملاحظة: هذه بيانات معروضة فقط. للتخزين الدائم، قم بنسخها إلى جوجل شيت")

# =====================================================
# 5. المتأخرات
# =====================================================
elif menu == "⚠️ المتأخرات":
    st.title("⚠️ كشف المتأخرات")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات")
    else:
        revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
        late = revenue[revenue["المتبقي"] > 0].copy()
        
        if not late.empty:
            total_late = late["المتبقي"].sum()
            col1, col2 = st.columns(2)
            col1.metric("💰 اجمالي المتأخرات", f"{int(total_late):,} جنيه")
            col2.metric("📊 عدد الوحدات المتأخرة", f"{len(late)} وحدة", delta=f"{len(late)} وحدة")
            
            st.subheader("📋 قائمة المتأخرات")
            late_display = late[["المالك", "الوحدة", "الدور", "شهر الاستحقاق", "الاشتراك", "المدفوع", "المتبقي", "ملاحظات"]]
            late_display = late_display.sort_values("المتبقي", ascending=False)
            st.dataframe(late_display, use_container_width=True)
            
            # تحميل التقرير
            csv = late_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل تقرير المتأخرات (CSV)",
                data=csv,
                file_name=f"متأخرات_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.success("🎉 لا توجد متأخرات! جميع الوحدات مسددة بالكامل.")
            st.balloons()

# =====================================================
# 6. التقارير الاحترافية
# =====================================================
elif menu == "📊 التقارير الاحترافية":
    st.title("📑 التقارير المالية الاحترافية")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات لعرض التقارير")
    else:
        all_m = get_sorted_months(revenue, "شهر الاستحقاق")
        if all_m:
            sel_m = st.selectbox("📅 اختر الشهر للتقرير:", all_m)
            
            col1, col2 = st.columns(2)
            with col1:
                include_details = st.checkbox("✅ تضمين تفاصيل الوحدات", value=True)
            with col2:
                show_chart = st.checkbox("✅ عرض الرسم البياني", value=True)
            
            if st.button("📄 توليد التقرير المفصل", use_container_width=True):
                df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
                df_e = expenses[expenses["الشهر"] == sel_m].copy() if not expenses.empty else pd.DataFrame()
                
                # حساب الإجماليات
                total_required = df_r["الاشتراك"].sum()
                total_paid = df_r["المدفوع"].sum()
                total_expenses = df_e["المبلغ"].sum() if not df_e.empty else 0
                net_profit = total_paid - total_expenses
                payment_rate = (total_paid / total_required * 100) if total_required > 0 else 0
                
                # عرض الملخص
                st.subheader(f"📊 ملخص شهر {sel_m}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("💰 المطلوب", f"{int(total_required):,} جنيه")
                c2.metric("✅ المحصل", f"{int(total_paid):,} جنيه")
                c3.metric("💸 المصاريف", f"{int(total_expenses):,} جنيه")
                c4.metric("📈 صافي الربح", f"{int(net_profit):,} جنيه")
                
                # نسبة التحصيل
                st.progress(payment_rate / 100)
                st.caption(f"📊 نسبة التحصيل: {payment_rate:.1f}%")
                
                # الرسم البياني
                if show_chart:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    categories = ['المطلوب', 'المحصل', 'المصاريف']
                    values = [total_required, total_paid, total_expenses]
                    colors = ['#3498db', '#2ecc71', '#e74c3c']
                    ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=1)
                    ax.set_ylabel('القيمة (جنيه)', fontsize=12)
                    ax.set_title(f'ملخص شهر {sel_m}', fontsize=14, fontweight='bold')
                    for i, v in enumerate(values):
                        ax.text(i, v + 10, f'{int(v):,}', ha='center', fontweight='bold')
                    st.pyplot(fig)
                
                # تفاصيل الإيرادات
                if include_details and not df_r.empty:
                    st.subheader("📋 كشف اشتراكات الوحدات")
                    df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                    df_r["الحالة"] = df_r["المتبقي"].apply(lambda x: "🔴 متأخر" if x > 0 else "🟢 مدفوع")
                    st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "المتبقي", "الحالة", "ملاحظات"]], use_container_width=True)
                
                # تفاصيل المصروفات
                if not df_e.empty:
                    st.subheader("💸 كشف المصروفات التفصيلي")
                    st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
                
                # إحصائيات إضافية
                st.subheader("📊 إحصائيات إضافية")
                stat1, stat2, stat3 = st.columns(3)
                stat1.metric("متوسط الاشتراك", f"{int(df_r['الاشتراك'].mean()):,} جنيه")
                stat2.metric("أعلى متأخر", f"{int(df_r['الاشتراك'].max() - df_r['المدفوع'].max()):,} جنيه")
                stat3.metric("عدد الدافعين كاملاً", f"{len(df_r[df_r['المتبقي'] == 0])} وحدة")
        else:
            st.info("📭 لا توجد شهور مسجلة في البيانات")

# =====================================================
# الشريط الجانبي - معلومات عامة
# =====================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 معلومات النظام")

if not revenue.empty:
    total_unpaid = (revenue['الاشتراك'] - revenue['المدفوع']).sum()
    st.sidebar.metric("💰 إجمالي المتأخرات", f"{int(total_unpaid):,} جنيه")
    st.sidebar.metric("🏢 عدد الوحدات", f"{len(revenue['الوحدة'].unique())} وحدة")
    st.sidebar.metric("📅 آخر تحديث", datetime.now().strftime("%Y-%m-%d"))

st.sidebar.markdown("---")

if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# تعليمات سريعة
with st.sidebar.expander("📖 تعليمات سريعة"):
    st.markdown("""
    **لإضافة بيانات جديدة:**
    1. افتح جوجل شيت
    2. أضف البيانات في الأوراق المخصصة
    3. ملف ← نشر على الويب ← تحديث
    4. اضغط زر التحديث هنا
    
    **للحصول على روابط CSV:**
    1. ملف ← نشر على الويب
    2. اختر الورقة
    3. اختر CSV
    4. انسخ الرابط
    5. ضعه في الكود
    """)
