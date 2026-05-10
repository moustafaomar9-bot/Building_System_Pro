import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد الصفحة
st.set_page_config(page_title="نظام إدارة العمارة", layout="wide")

# دالة معالجة العربي
def ar(text):
    if pd.isna(text) or text == "": 
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# ⚠️ ضع هنا الرابط الذي نسخته من خطوة النشر ⚠️
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVG3VxOUGh0YgFlKGZlhO1e0iurf3Pu0w0e35u2F72mz2dL3UHtbbz6xx63uP8Uefz9MFmJ-gW4eOV/pub?output=csv"

# تحميل البيانات مباشرة من رابط CSV
@st.cache_data(ttl=60)
def load_data():
    try:
        # قراءة البيانات مباشرة من رابط CSV
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        
        # إعادة تسمية الأعمدة حسب ما يتوقعه البرنامج
        # شوف الأعمدة الموجودة في ملفك من الصورة:
        # الدور, الوحدة, المالك, شهر الاستحقاق, الاشتراك, المدفوع, ملاحظات
        
        # تأكد من وجود الأعمدة المطلوبة
        required_columns = ['الدور', 'الوحدة', 'المالك', 'شهر الاستحقاق', 'الاشتراك', 'المدفوع']
        
        # إذا كانت الأعمدة بأسماء مختلفة، غيرها هنا
        # مثال: إذا كان اسم عمود المالك هو "صاحب الوحدة"
        # column_mapping = {'صاحب الوحدة': 'المالك'}
        # df = df.rename(columns=column_mapping)
        
        # تحويل الأعمدة الرقمية
        df['الاشتراك'] = pd.to_numeric(df['الاشتراك'], errors='coerce').fillna(0)
        df['المدفوع'] = pd.to_numeric(df['المدفوع'], errors='coerce').fillna(0)
        
        # تنظيف الشهور
        df['شهر الاستحقاق'] = df['شهر الاستحقاق'].astype(str).str.strip()
        
        # التأكد من وجود عمود الملاحظات
        if 'ملاحظات' not in df.columns:
            df['ملاحظات'] = ""
        
        st.success(f"✅ تم تحميل {len(df)} سجل بنجاح!")
        return df
        
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
        st.info("""
        **الحل:**
        1. افتح جوجل شيت
        2. اضغط على ملف ← مشاركة ← نشر على الويب
        3. اختر الورقة ← CSV ← نشر
        4. انسخ الرابط وضعه في المتغير GOOGLE_SHEET_CSV_URL
        """)
        return pd.DataFrame()

# تحميل البيانات
revenue = load_data()
expenses = pd.DataFrame()  # مصروفات - يمكن إضافتها لاحقاً

def get_sorted_months(df, col):
    if df.empty or col not in df.columns:
        return []
    months = [str(m) for m in df[col].unique() if str(m).strip() and str(m).lower() != 'nan' and str(m) != '']
    return sorted(months, reverse=True)

menu = st.sidebar.radio("📋 القائمة الرئيسية", ["🏠 لوحة التحكم", "💰 الإيرادات", "⚠️ المتأخرات", "📊 التقارير"])

if menu == "🏠 لوحة التحكم":
    st.title("📊 ملخص المركز المالي")
    
    if revenue.empty:
        st.info("📭 لا توجد بيانات")
        st.markdown("""
        ### خطوات ربط جوجل شيت:
        
        1. **افتح جوجل شيت** من [هذا الرابط](https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw/edit)
        
        2. **اذهب إلى: ملف ← مشاركة ← نشر على الويب**
        
        3. **اختر الورقة** التي فيها البيانات
        
        4. **اختر CSV** من القائمة
        
        5. **اضغط نشر** وانسخ الرابط
        
        6. **الصق الرابط** في الكود (السطر 22)
        
        7. **اضغط على زر التحديث** 👇
        """)
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
            col3.metric("📈 المتبقي", f"{int(net):,} جنيه")
            
            # الرسم البياني
            fig, ax = plt.subplots(figsize=(10, 5))
            categories = [ar("المطلوب"), ar("المحصل")]
            values = [t_sub, t_paid]
            colors = ['#3498db', '#2ecc71']
            bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=2)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, f'{int(val):,}', ha='center', va='bottom', fontweight='bold', fontsize=12)
            ax.set_ylabel("القيمة (جنيه)", fontsize=12)
            ax.set_title(f"🏢 الملخص المالي لشهر {sel_m}", fontsize=16, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            
            # عرض الجدول
            st.subheader("📋 تفاصيل الإيرادات")
            df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
            df_r["الحالة"] = df_r["المتبقي"].apply(lambda x: "🔴 متأخر" if x > 0 else "🟢 مدفوع")
            
            # اختيار الأعمدة الموجودة
            display_cols = []
            for col in ['الدور', 'الوحدة', 'المالك', 'الاشتراك', 'المدفوع', 'المتبقي', 'الحالة', 'ملاحظات']:
                if col in df_r.columns:
                    display_cols.append(col)
            
            st.dataframe(df_r[display_cols], use_container_width=True)
        else:
            st.info("لا توجد شهور")

elif menu == "💰 الإيرادات":
    st.title("💰 جدول الإيرادات")
    if revenue.empty:
        st.warning("⚠️ لا توجد بيانات")
    else:
        st.dataframe(revenue, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        total_required = revenue['الاشتراك'].sum()
        total_paid = revenue['المدفوع'].sum()
        col1.metric("اجمالي المطلوب", f"{int(total_required):,} جنيه")
        col2.metric("اجمالي المحصل", f"{int(total_paid):,} جنيه")
        col3.metric("المتبقي", f"{int(total_required - total_paid):,} جنيه")

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
            
            display_cols = []
            for col in ['المالك', 'الوحدة', 'الدور', 'شهر الاستحقاق', 'الاشتراك', 'المدفوع', 'المتبقي']:
                if col in late.columns:
                    display_cols.append(col)
            
            st.dataframe(late[display_cols], use_container_width=True)
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
                
                col1, col2, col3 = st.columns(3)
                col1.metric("المطلوب", f"{int(total_required):,} جنيه")
                col2.metric("المحصل", f"{int(total_paid):,} جنيه")
                col3.metric("نسبة التحصيل", f"{int((total_paid/total_required)*100) if total_required > 0 else 0}%")
                
                df_r["المتبقي"] = df_r["الاشتراك"] - df_r["المدفوع"]
                display_cols = []
                for col in ['الدور', 'الوحدة', 'المالك', 'الاشتراك', 'المدفوع', 'المتبقي']:
                    if col in df_r.columns:
                        display_cols.append(col)
                st.dataframe(df_r[display_cols], use_container_width=True)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
