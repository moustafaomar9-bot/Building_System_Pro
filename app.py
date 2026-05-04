
5. **اذهب إلى ملف -> نشر على الويب**

6. **اختر ورقة revenue** -> اختر CSV -> اضغط نشر

7. **انسخ الرابط** واستبدله في الكود (REVENUE_CSV_URL)

8. **كرر الخطوات 5-7** لورقة expenses

9. **اضغط زر التحديث** في الشريط الجانبي
""")

# =====================================================
# القائمة الجانبية
# =====================================================
menu = st.sidebar.radio(
"📋 القائمة الرئيسية",
["🏠 لوحة التحكم", "💰 الايرادات", "💸 المصروفات", "⚠️ المتاخرات", "📊 التقارير"]
)

# =====================================================
# 1. لوحة التحكم
# =====================================================
if menu == "🏠 لوحة التحكم":
st.title("📊 ملخص المركز المالي")

if revenue.empty:
st.info("📭 لا توجد بيانات. يرجى اتباع التعليمات في الشريط الجانبي")

# عرض نموذج للبيانات
st.subheader("📝 نموذج بيانات الايرادات")
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

st.subheader("📝 نموذج بيانات المصروفات")
sample_exp = pd.DataFrame({
 "التاريخ": ["2025-01-15", "2025-01-20"],
 "الشهر": ["01/2025", "01/2025"],
 "النوع": ["كهرباء", "نظافة"],
 "التفاصيل": ["فاتورة الكهرباء", "راتب العامل"],
 "المبلغ": [300, 200]
})
st.dataframe(sample_exp, use_container_width=True)

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
 
 # عرض المؤشرات
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
 
 # اضافة الارقام على الاعمدة
 for bar, val in zip(bars, values):
     ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, 
            f'{int(val):,}', ha='center', va='bottom', fontweight='bold', fontsize=12)
 
 ax.set_ylabel("القيمة (جنيه)", fontsize=12)
 ax.set_title(f"🏢 الملخص المالي لشهر {sel_m}", fontsize=16, fontweight='bold')
 ax.grid(axis='y', alpha=0.3)
 st.pyplot(fig)
 
 # عرض جدول التفاصيل
 with st.expander("📋 تفاصيل الايرادات"):
     st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "ملاحظات"]], use_container_width=True)
 
 if not df_e.empty:
     with st.expander("💸 تفاصيل المصروفات"):
         st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
else:
 st.info("لا توجد شهور مسجلة. قم باضافة البيانات في جوجل شيت")

# =====================================================
# 2. الإيرادات
# =====================================================
elif menu == "💰 الايرادات":
st.title("💰 جدول الايرادات")

if revenue.empty:
st.warning("⚠️ لا توجد بيانات ايرادات")
st.markdown("""
### كيفية اضافة البيانات:
1. افتح جوجل شيت
2. اذهب الى ورقة `revenue`
3. اضف البيانات حسب النموذج اعلاه
4. ثم اضغط على زر التحديث في الشريط الجانبي
""")
else:
# عرض جميع الايرادات
st.dataframe(revenue, use_container_width=True)

# احصائيات سريعة
st.subheader("📊 احصائيات سريعة")
col1, col2, col3 = st.columns(3)
col1.metric("اجمالي المطلوب", f"{int(revenue['الاشتراك'].sum()):,} جنيه")
col2.metric("اجمالي المحصل", f"{int(revenue['المدفوع'].sum()):,} جنيه")
col3.metric("المتبقي", f"{int(revenue['الاشتراك'].sum() - revenue['المدفوع'].sum()):,} جنيه")

# =====================================================
# 3. المصاريف
# =====================================================
elif menu == "💸 المصروفات":
st.title("💸 جدول المصروفات")

if expenses.empty:
st.warning("⚠️ لا توجد بيانات مصروفات")
st.markdown("""
### كيفية اضافة البيانات:
1. افتح جوجل شيت
2. اذهب الى ورقة `expenses`
3. اضف البيانات حسب النموذج اعلاه
4. ثم اضغط على زر التحديث في الشريط الجانبي
""")
else:
# عرض جميع المصروفات
st.dataframe(expenses, use_container_width=True)

# احصائيات سريعة
total_exp = expenses['المبلغ'].sum()
st.metric("اجمالي المصروفات", f"{int(total_exp):,} جنيه")

# عرض المصروفات حسب النوع
if 'النوع' in expenses.columns:
 st.subheader("📊 المصروفات حسب النوع")
 exp_by_type = expenses.groupby('النوع')['المبلغ'].sum().sort_values(ascending=False)
 st.bar_chart(exp_by_type)

# =====================================================
# 4. المتأخرات
# =====================================================
elif menu == "⚠️ المتاخرات":
st.title("⚠️ كشف المتاخرات")

if revenue.empty:
st.info("لا توجد بيانات")
else:
# حساب المتبقي لكل سجل
revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
late = revenue[revenue["المتبقي"] > 0].copy()

if not late.empty:
 total_late = late["المتبقي"].sum()
 
 col1, col2 = st.columns(2)
 col1.metric("💰 اجمالي المتاخرات", f"{int(total_late):,} جنيه")
 col2.metric("📊 عدد الوحدات المتاخرة", f"{len(late)} وحدة")
 
 # عرض المتاخرات في جدول مرتب
 st.subheader("📋 قائمة المتاخرات")
 late_display = late[["المالك", "الوحدة", "الدور", "شهر الاستحقاق", "الاشتراك", "المدفوع", "المتبقي", "ملاحظات"]]
 late_display = late_display.sort_values("المتبقي", ascending=False)
 st.dataframe(late_display, use_container_width=True)
 
 # تحميل التقرير
 csv = late_display.to_csv(index=False).encode('utf-8-sig')
 st.download_button(
     label="📥 تحميل تقرير المتاخرات (CSV)",
     data=csv,
     file_name=f"متاخرات_{datetime.now().strftime('%Y%m%d')}.csv",
     mime="text/csv",
     use_container_width=True
 )
else:
 st.success("🎉 لا توجد متاخرات! جميع الوحدات مسددة بالكامل.")
 st.balloons()

# =====================================================
# 5. التقارير
# =====================================================
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
     # حساب الاجماليات
     total_required = df_r["الاشتراك"].sum()
     total_paid = df_r["المدفوع"].sum()
     total_expenses = df_e["المبلغ"].sum() if not df_e.empty else 0
     net_profit = total_paid - total_expenses
     
     # عرض الملخص
     st.subheader(f"📊 ملخص شهر {sel_m}")
     col1, col2, col3, col4 = st.columns(4)
     col1.metric("المطلوب", f"{int(total_required):,} جنيه")
     col2.metric("المحصل", f"{int(total_paid):,} جنيه")
     col3.metric("المصاريف", f"{int(total_expenses):,} جنيه")
     col4.metric("صافي الربح", f"{int(net_profit):,} جنيه")
     
     # عرض الجداول
     st.subheader("📋 تفاصيل الايرادات")
     st.dataframe(df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع"]], use_container_width=True)
     
     if not df_e.empty:
         st.subheader("💸 تفاصيل المصروفات")
         st.dataframe(df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]], use_container_width=True)
     
     # رسم بياني
     fig, ax = plt.subplots(figsize=(8, 4))
     categories = ['المطلوب', 'المحصل', 'المصاريف']
     values = [total_required, total_paid, total_expenses]
     colors = ['#3498db', '#2ecc71', '#e74c3c']
     ax.bar(categories, values, color=colors, width=0.5)
     ax.set_ylabel('القيمة (جنيه)')
     ax.set_title(f'ملخص شهر {sel_m}')
     st.pyplot(fig)
else:
 st.info("لا توجد شهور مسجلة")

# =====================================================
# الشريط الجانبي - معلومات وازرار
# =====================================================
st.sidebar.markdown("---")

# عرض معلومات النظام
if not revenue.empty:
st.sidebar.info(f"""
📌 **معلومات النظام**
- 📅 اليوم: {datetime.now().strftime("%Y-%m-%d")}
- 🏢 عدد الوحدات: {len(revenue["الوحدة"].unique()) if "الوحدة" in revenue.columns else 0}
- 💰 اجمالي المتاخرات: {int((revenue['الاشتراك'] - revenue['المدفوع']).sum()) if 'الاشتراك' in revenue.columns else 0} جنيه
""")

# زر تحديث البيانات
if st.sidebar.button("🔄 تحديث البيانات", use_container_width=True):
st.cache_data.clear()
st.rerun()

# رابط سريع لجوجل شيت
st.sidebar.markdown("---")
st.sidebar.markdown("[📊 فتح جوجل شيت](https://docs.google.com/spreadsheets/d/1_X5q3PkdJHbgiLCqZICsFEQdSVzAsDwjC2gN5mHYuuw/edit)")
