
4. **اختر صلاحية محرر (Editor)** من القائمة المنسدلة

5. **اضغط على إرسال (Send)**

6. **انتظر 2-3 دقائق** ثم اضغط على F5 او Ctrl+R لتحديث الصفحة

### ملاحظات مهمة:
- تاكد من وجود ورقتين عمل في الجوجل شيت باسم revenue و expenses
- اذا لم تكن موجودة قم باضافتهما بنفس الاسماء تماما
""")

# =====================================================
# القائمة الجانبية
# =====================================================
menu = st.sidebar.radio(
"📋 القائمة الرئيسية",
["🏠 لوحة التحكم", "💰 الإيرادات", "💸 المصاريف", "🆕 بدء شهر جديد", "⚠️ المتأخرات", "📊 التقارير الاحترافية"]
)

# =====================================================
# 1. لوحة التحكم
# =====================================================
if menu == "🏠 لوحة التحكم":
st.title("📊 ملخص المركز المالي")

if revenue.empty:
st.info("لا توجد بيانات ايرادات لعرضها. ابدا باضافة البيانات من قائمة الايرادات")
else:
all_m = get_sorted_months(revenue, "شهر الاستحقاق")
if all_m:
    col1, col2 = st.columns([1, 2])
    with col1:
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
    bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', linewidth=1)
    
    # اضافة الارقام على الاعمدة
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100, 
               f'{int(val):,}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel("القيمة (جنيه)", fontsize=12)
    ax.set_title(f"الملخص المالي لشهر {sel_m}", fontsize=16, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    st.pyplot(fig)
else:
    st.info("لا توجد شهور مسجلة. ابدا باضافة البيانات من قائمة الايرادات")

# =====================================================
# 2. الإيرادات
# =====================================================
elif menu == "💰 الإيرادات":
st.title("💰 ادارة الايرادات")

if revenue.empty:
st.warning("لا توجد بيانات ايرادات. قم باضافة البيانات يدويا في الجوجل شيت اولا")

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
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("حفظ التعديلات", use_container_width=True):
            others = revenue[revenue["شهر الاستحقاق"] != sel_m]
            save_all(pd.concat([others, edited_rev], ignore_index=True), expenses)
            st.rerun()
    with col2:
        if st.button("تحديث البيانات", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# =====================================================
# 3. المصاريف
# =====================================================
elif menu == "💸 المصاريف":
st.title("💸 ادارة المصروفات")

# الحصول على قائمة الشهور من الايرادات
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
            e_month = st.text_input("الشهر (مثال: 01/2026)", datetime.now().strftime("%m/%Y"))
        e_det = st.text_area("التفاصيل", placeholder="ادخل تفاصيل المصروف...")
    
    submitted = st.form_submit_button("حفظ المصروف", use_container_width=True)
    
    if submitted:
        if e_amt <= 0:
            st.error("المبلغ يجب ان يكون اكبر من صفر")
        else:
            new_exp = pd.DataFrame([[
                e_date.strftime("%Y-%m-%d"), 
                e_month, 
                e_type, 
                e_det, 
                e_amt
            ]], columns=expenses.columns if not expenses.empty else ["التاريخ", "الشهر", "النوع", "التفاصيل", "المبلغ"])
            
            if save_all(revenue, pd.concat([expenses, new_exp], ignore_index=True)):
                st.success("تم تسجيل المصروف بنجاح!")
                st.rerun()

with tab2:
if not expenses.empty and all_m:
    sel_m_view = st.selectbox("عرض مصروفات شهر:", all_m, key="exp_view")
    m_exp = expenses[expenses["الشهر"] == sel_m_view].copy()
    
    if not m_exp.empty:
        st.subheader(f"تعديل مصروفات شهر {sel_m_view}")
        ed_exp = st.data_editor(m_exp, num_rows="dynamic", use_container_width=True, key="exp_ed")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("حفظ التعديلات", use_container_width=True, key="save_exp"):
                other_exp = expenses[expenses["الشهر"] != sel_m_view]
                save_all(revenue, pd.concat([other_exp, ed_exp], ignore_index=True))
                st.rerun()
        with col2:
            if st.button("حذف الكل", use_container_width=True, key="del_exp"):
                other_exp = expenses[expenses["الشهر"] != sel_m_view]
                save_all(revenue, other_exp)
                st.rerun()
    else:
        st.info(f"لا توجد مصروفات مسجلة لشهر {sel_m_view}")
elif expenses.empty:
    st.info("لا توجد مصروفات مسجلة حتى الان")
else:
    st.info("قم باضافة ايرادات اولا لتظهر لك قائمة الشهور")

# =====================================================
# 4. بدء شهر جديد
# =====================================================
elif menu == "🆕 بدء شهر جديد":
st.title("🆕 ترحيل البيانات لشهر جديد")

if revenue.empty:
st.warning("لا توجد بيانات سابقة للترحيل. قم باضافة البيانات اولا")
else:
all_m = get_sorted_months(revenue, "شهر الاستحقاق")
if all_m:
    col1, col2 = st.columns(2)
    
    with col1:
        last_m = st.selectbox("نسخ البيانات من شهر:", all_m)
    
    with col2:
        default_new = datetime.now().strftime("%m/%Y")
        new_m = st.text_input("الشهر الجديد (مثال: 03/2026):", default_new)
    
    st.info(f"سيتم نسخ جميع الوحدات من شهر {last_m} الى شهر {new_m} مع اعادة تعيين المدفوعات الى صفر")
    
    if st.button("تنفيذ الترحيل الان", use_container_width=True):
        if new_m in all_m:
            st.error(f"الشهر {new_m} موجود بالفعل!")
        elif new_m == "" or new_m is None:
            st.warning("برجاء كتابة اسم الشهر الجديد")
        else:
            last_data = revenue[revenue["شهر الاستحقاق"] == last_m].copy()
            new_rows = []
            
            for _, row in last_data.iterrows():
                debt = row["الاشتراك"] - row["المدفوع"]
                note = f"متاخرات من {last_m}: {int(debt)} جنيه" if debt > 0 else "مسدد بالكامل"
                
                new_rows.append([
                    row["الدور"], 
                    row["الوحدة"], 
                    row["المالك"], 
                    new_m, 
                    row["الاشتراك"], 
                    0, 
                    note
                ])
            
            new_month_data = pd.DataFrame(new_rows, columns=revenue.columns)
            updated_revenue = pd.concat([revenue, new_month_data], ignore_index=True)
            
            if save_all(updated_revenue, expenses):
                st.balloons()
                st.success(f"تم ترحيل البيانات الى شهر {new_m} بنجاح!")
                st.rerun()
else:
    st.error("لا توجد شهور متاحة للنسخ منها")

# =====================================================
# 5. المتأخرات
# =====================================================
elif menu == "⚠️ المتأخرات":
st.title("⚠️ كشف المتاخرات")

if revenue.empty:
st.info("لا توجد بيانات لعرض المتاخرات")
else:
# حساب المتبقي لكل سجل
revenue["المتبقي"] = revenue["الاشتراك"] - revenue["المدفوع"]
late = revenue[revenue["المتبقي"] > 0].copy()

if not late.empty:
    total_late = late["المتبقي"].sum()
    st.metric("اجمالي المتاخرات", f"{int(total_late):,} جنيه", delta=f"{len(late)} وحدة متاخرة")
    
    # عرض المتاخرات في جدول مرتب
    late_display = late[["المالك", "الوحدة", "الدور", "شهر الاستحقاق", "الاشتراك", "المدفوع", "المتبقي", "ملاحظات"]]
    late_display = late_display.sort_values("المتبقي", ascending=False)
    
    st.dataframe(late_display, use_container_width=True)
    
    # تحميل التقرير
    csv = late_display.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="تحميل تقرير المتاخرات (CSV)",
        data=csv,
        file_name=f"متاخرات_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.success("لا توجد متاخرات! جميع الوحدات مسددة بالكامل.")

# =====================================================
# 6. التقارير الاحترافية
# =====================================================
elif menu == "📊 التقارير الاحترافية":
st.title("📑 التقارير المالية الاحترافية")

if revenue.empty:
st.info("لا توجد بيانات لعرض التقارير")
else:
all_m = get_sorted_months(revenue, "شهر الاستحقاق")
if all_m:
    sel_m = st.selectbox("اختر الشهر للتقرير:", all_m)
    
    col1, col2 = st.columns(2)
    with col1:
        include_expenses = st.checkbox("تضمين المصروفات", value=True)
    with col2:
        include_details = st.checkbox("تضمين تفاصيل الوحدات", value=True)
    
    if st.button("توليد التقرير المفصل", use_container_width=True):
        df_r = revenue[revenue["شهر الاستحقاق"] == sel_m].copy()
        df_e = expenses[expenses["الشهر"] == sel_m].copy() if include_expenses and not expenses.empty else pd.DataFrame()
        
        # اعداد حالة الحساب
        def get_status(row):
            d = row['الاشتراك'] - row['المدفوع']
            if d > 0:
                return f'مطلوب: {int(d):,}'
            elif d < 0:
                return f'له: {int(abs(d)):,}'
            return 'مسدد'
        
        df_r["حالة الحساب"] = df_r.apply(get_status, axis=1)
        
        # حساب الاجماليات
        total_required = df_r["الاشتراك"].sum()
        total_paid = df_r["المدفوع"].sum()
        total_expenses = df_e["المبلغ"].sum() if not df_e.empty else 0
        net_profit = total_paid - total_expenses
        
        # انشاء التقرير
        report_html = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>التقرير المالي - {sel_m}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #1e3c72; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                th {{ background-color: #1e3c72; color: white; }}
                .summary {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .card {{ background: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center; flex: 1; margin: 0 10px; }}
            </style>
        </head>
        <body>
            <h1>التقرير المالي لشهر {sel_m}</h1>
            <p>تاريخ التقرير: {datetime.now().strftime('%Y/%m/%d')}</p>
            
            <div class="summary">
                <div class="card"><strong>المطلوب</strong><br>{int(total_required):,} جنيه</div>
                <div class="card"><strong>المحصل</strong><br>{int(total_paid):,} جنيه</div>
                <div class="card"><strong>المصاريف</strong><br>{int(total_expenses):,} جنيه</div>
                <div class="card"><strong>صافي الربح</strong><br>{int(net_profit):,} جنيه</div>
            </div>
        """
        
        if include_details and not df_r.empty:
            report_html += f"""
            <h2>تفاصيل الايرادات</h2>
            {df_r[["الدور", "الوحدة", "المالك", "الاشتراك", "المدفوع", "حالة الحساب"]].to_html(index=False, escape=False)}
            """
        
        if include_expenses and not df_e.empty:
            report_html += f"""
            <h2>تفاصيل المصروفات</h2>
            {df_e[["التاريخ", "النوع", "التفاصيل", "المبلغ"]].to_html(index=False)}
            """
        
        report_html += "</body></html>"
        
        # عرض التقرير
        st.components.v1.html(report_html, height=600, scrolling=True)
        
        # زر التحميل
        st.download_button(
            label=f"تحميل تقرير شهر {sel_m} (HTML)",
            data=report_html,
            file_name=f"تقرير_{sel_m}.html",
            mime="text/html",
            use_container_width=True
        )
else:
    st.info("لا توجد شهور مسجلة في البيانات")

# شريط جانبي - معلومات اضافية
st.sidebar.markdown("---")
st.sidebar.info(
f"""
📌 **معلومات النظام**

- متصل بجوجل شيت
- اخر تحديث: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- عدد الوحدات: {len(revenue["الوحدة"].unique()) if not revenue.empty else 0}
"""
)

if st.sidebar.button("تحديث البيانات", use_container_width=True):
st.cache_data.clear()
st.rerun()
