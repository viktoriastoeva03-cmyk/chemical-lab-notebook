import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.set_page_config(page_title="Електрохимия & Лабораторен Дневник", layout="wide")

st.title("🧪 Електрохимия & Лабораторен Дневник")
st.write("Масово качване на файлове, Свали/Отвори оригинален Excel файл от телефон и Управление")

# Папка за съхранение на оригиналните качени Excel/CSV файлове
FILES_DIR = "uploaded_files"
os.makedirs(FILES_DIR, exist_ok=True)

# Файлове за базата данни
EXP_FILE = "experiments_v2.csv"
BATTERIES_FILE = "batteries_v2.csv"
ABRIN_FILE = "abrin_channels.csv"

def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(file_path, encoding='utf-8')
        df = df.dropna(how='all').fillna("")
        return df
    return pd.DataFrame(columns=columns)

def categorize_battery(row):
    material = str(row.get("Тип клетка / Състав", "")).lower()
    name = str(row.get("Име на Папка/Батерия", "")).lower()
    text = name + " " + material
    
    if "na" in text or "sodium" in text or "натри" in text:
        chem = "Na-ion (Натриева)"
    elif "li" in text or "lithium" in text or "лити" in text:
        chem = "Li-ion (Литиева)"
    else:
        chem = "Други / Неопределен"

    date_str = str(row.get("Дата на сглобяване", ""))
    year = date_str.split("-")[0] if "-" in date_str and len(date_str.split("-")[0]) == 4 else "2026"

    return chem, year

# Зареждане на данните
df_exp = load_data(EXP_FILE, ["ID", "Кога (Дата)", "Име на Батерия/Клетка", "Изследовател", "Заглавие", "Какво е направено", "Защо е направено (Цел)", "Органична формула (SMILES/LaTeX)", "Параметри"])
df_batt = load_data(BATTERIES_FILE, ["Име на Папка/Батерия", "Дата на сглобяване", "Партиден №", "Тип клетка / Състав", "Цел / Назначение", "Оригинален Файл"])
df_abrin = load_data(ABRIN_FILE, ["Канал", "Име на Клетка / Батерия", "Забележка", "Дата на поставяне"])

menu = st.sidebar.radio("📋 Модули", [
    "📁 Папки: Клетки / Батерии & Сортиране",
    "🔌 Абрин: Разпределение по Канали",
    "📝 Нов Лабораторен Опит",
    "📚 Пълен Архив (Редакция & Изтриване)",
    "📊 Анализ & Графики"
])

# 1. МОДУЛ: ПАПКИ И БАТЕРИИ + КАЧВАНЕ НА ОРИГИНАЛНИ ФАЙЛОВЕ
if menu == "📁 Папки: Клетки / Батерии & Сортиране":
    st.header("📁 Батерии & Клетки (Масово качване + Запазване на Excel файлове)")
    
    tab1, tab2 = st.tabs(["➕ Ръчно добавяне", "📂 Масово качване (до 100 CSV/Excel файла)"])
    
    with tab1:
        with st.form("battery_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                b_name = st.text_input("Име на Клетката", "Cell_Li_NMC_01")
                b_date = st.date_input("Дата на сглобяване", datetime.now())
            with col2:
                b_num = st.text_input("Партиден №", "BATT-2026-001")
                b_type = st.text_input("Материал / Състав", "Li-ion / NMC / Графит")
            with col3:
                b_target = st.text_area("Цел", "Тест при висок ток")
                
            submit_b = st.form_submit_button("📁 Запази клетка")
            if submit_b:
                new_b = pd.DataFrame([{
                    "Име на Папка/Батерия": b_name,
                    "Дата на сглобяване": b_date.strftime("%Y-%m-%d"),
                    "Партиден №": b_num,
                    "Тип клетка / Състав": b_type,
                    "Цел / Назначение": b_target,
                    "Оригинален Файл": ""
                }])
                df_batt_updated = pd.concat([df_batt, new_b], ignore_index=True)
                df_batt_updated.to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                st.success(f"Клетката '{b_name}' беше запазена!")
                st.rerun()

    with tab2:
        st.subheader("📥 Качете до 100 Excel или CSV файла наведнъж")
        st.write("Качените файлове се запазват в системата и могат да се свалят от телефон/компютър по всяко време.")
        
        uploaded_files = st.file_uploader(
            "Изберете файлове от компютъра (CSV/XLSX)", 
            type=["csv", "xlsx"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.info(f"Избрани файлове за обработка: **{len(uploaded_files)}**")
            
            if st.button("🚀 Добави всички качени файлове към базата данни"):
                new_entries = []
                for file in uploaded_files:
                    try:
                        base_name = os.path.splitext(file.name)[0]
                        saved_path = os.path.join(FILES_DIR, file.name)
                        
                        # Запазваме оригиналния файл във папката uploaded_files
                        with open(saved_path, "wb") as f:
                            f.write(file.getbuffer())
                        
                        if file.name.endswith('.csv'):
                            temp_df = pd.read_csv(saved_path)
                        else:
                            temp_df = pd.read_excel(saved_path)
                        
                        if "Име на Папка/Батерия" in temp_df.columns:
                            for _, row in temp_df.iterrows():
                                new_entries.append({
                                    "Име на Папка/Батерия": row.get("Име на Папка/Батерия", base_name),
                                    "Дата на сглобяване": row.get("Дата на сглобяване", datetime.now().strftime("%Y-%m-%d")),
                                    "Партиден №": row.get("Партиден №", "IMPORTED"),
                                    "Тип клетка / Състав": row.get("Тип клетка / Състав", base_name),
                                    "Цел / Назначение": row.get("Цел / Назначение", f"Импортиран от {file.name}"),
                                    "Оригинален Файл": file.name
                                })
                        else:
                            new_entries.append({
                                "Име на Папка/Батерия": base_name,
                                "Дата на сглобяване": datetime.now().strftime("%Y-%m-%d"),
                                "Партиден №": "RAW-DATA",
                                "Тип клетка / Състав": base_name,
                                "Цел / Назначение": f"Данни от файл: {file.name}",
                                "Оригинален Файл": file.name
                            })
                    except Exception as e:
                        st.warning(f"Грешка при обработка на {file.name}: {e}")
                
                if new_entries:
                    imported_df = pd.DataFrame(new_entries)
                    df_batt_updated = pd.concat([df_batt, imported_df], ignore_index=True).drop_duplicates(subset=["Име на Папка/Батерия"])
                    df_batt_updated.to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                    st.success(f"Успешно добавени {len(new_entries)} клетки и техните файлове!")
                    st.rerun()

    st.markdown("---")
    st.subheader("🔍 Сортиран архив на клетките (С преглед на Excel файлове)")
    
    df_batt_clean = df_batt[df_batt["Име на Папка/Батерия"].astype(str).str.strip() != ""].copy()
    
    if not df_batt_clean.empty:
        df_batt_clean[["Химия (Li/Na)", "Година"]] = df_batt_clean.apply(categorize_battery, axis=1, result_type="expand")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            chem_filter = st.selectbox("Филтър по Химия", ["Всички", "Li-ion (Литиева)", "Na-ion (Натриева)", "Други / Неопределен"])
        with col_f2:
            years_list = ["Всички"] + sorted([y for y in df_batt_clean["Година"].unique() if y], reverse=True)
            year_filter = st.selectbox("Филтър по Година", years_list)
        with col_f3:
            search_mat = st.text_input("Търси по материал/име", "")

        filtered_batt = df_batt_clean.copy()
        if chem_filter != "Всички":
            filtered_batt = filtered_batt[filtered_batt["Химия (Li/Na)"] == chem_filter]
        if year_filter != "Всички":
            filtered_batt = filtered_batt[filtered_batt["Година"] == year_filter]
        if search_mat:
            filtered_batt = filtered_batt[
                filtered_batt["Тип клетка / Състав"].astype(str).str.contains(search_mat, case=False, na=False) |
                filtered_batt["Име на Папка/Батерия"].astype(str).str.contains(search_mat, case=False, na=False)
            ]

        for idx, row in filtered_batt.iterrows():
            name_disp = row['Име на Папка/Батерия'] if row['Име на Папка/Батерия'] else "Без име"
            date_disp = row['Дата на сглобяване'] if row['Дата на сглобяване'] else "Няма дата"
            comp_disp = row['Тип клетка / Състав'] if row['Тип клетка / Състав'] else "Няма информация"
            file_name = str(row.get('Оригинален Файл', '')).strip()
            
            col_info, col_file, col_del = st.columns([5, 2, 1])
            with col_info:
                st.markdown(f"🔋 **{name_disp}** | 🧪 **{row['Химия (Li/Na)']}** | 📅 **{date_disp}** (Година: {row['Година']}) | ⚙️ **Състав:** {comp_disp}")
            
            with col_file:
                # Бутон за изтегляне/отваряне на Excel файла от телефон или компютър
                file_path = os.path.join(FILES_DIR, file_name) if file_name else ""
                if file_name and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"📥 Свали/Отвори Excel",
                            data=f,
                            file_name=file_name,
                            mime="application/octet-stream",
                            key=f"dl_{idx}"
                        )
                else:
                    st.caption("Няма прикачен файл")
                    
            with col_del:
                if st.button("🗑️ Изтрий", key=f"del_cell_{idx}"):
                    df_batt_updated = df_batt.drop(idx)
                    df_batt_updated.to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                    # Изтриване и на файла, ако съществува
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
                    st.success("Изтрито!")
                    st.rerun()
    else:
        st.info("Все още няма качени или създадени клетки.")

# 2. МОДУЛ: АБРИН
elif menu == "🔌 Абрин: Разпределение по Канали":
    st.header("🔌 Разпределение по канали в Абрин")
    abrin_dict = {str(row["Канал"]): row for idx, row in df_abrin.iterrows()} if not df_abrin.empty else {}
    
    for row_idx in range(2):
        cols = st.columns(4)
        for col_idx in range(4):
            ch_num = row_idx * 4 + col_idx + 1
            ch_key = f"Канал {ch_num}"
            with cols[col_idx]:
                if ch_key in abrin_dict and str(abrin_dict[ch_key]["Име на Клетка / Батерия"]).strip() != "":
                    cell_info = abrin_dict[ch_key]
                    st.error(f"### 🔴 {ch_key}\n\n**ЗАЕТ от:**\n\n🔋 **{cell_info['Име на Клетка / Батерия']}**\n\n⚙️ {cell_info['Забележка']}")
                    if st.button(f"🗑️ Освободи", key=f"clear_{ch_num}"):
                        df_abrin_updated = df_abrin[df_abrin["Канал"] != ch_key]
                        df_abrin_updated.to_csv(ABRIN_FILE, index=False, encoding='utf-8-sig')
                        st.rerun()
                else:
                    st.success(f"### 🟢 {ch_key}\n\n**Свободен**")

    st.markdown("---")
    with st.form("abrin_form"):
        col1, col2 = st.columns(2)
        with col1:
            channel_select = st.selectbox("Изберете Канал", [f"Канал {i}" for i in range(1, 9)])
            cell_options = df_batt["Име на Папка/Батерия"].tolist() if not df_batt.empty else ["Няма създадени клетки"]
            selected_cell = st.selectbox("Изберете Клетка", cell_options)
        with col2:
            ch_notes = st.text_input("Параметри", "0.1 mA, 2.8-4.2V")
            ch_date = st.date_input("Дата", datetime.now())
        if st.form_submit_button("Запази в канала"):
            if selected_cell != "Няма създадени клетки":
                df_abrin_clean = df_abrin[df_abrin["Канал"] != channel_select]
                new_ch = pd.DataFrame([{"Канал": channel_select, "Име на Клетка / Батерия": selected_cell, "Забележка": ch_notes, "Дата на поставяне": ch_date.strftime("%Y-%m-%d")}])
                pd.concat([df_abrin_clean, new_ch], ignore_index=True).to_csv(ABRIN_FILE, index=False, encoding='utf-8-sig')
                st.rerun()

# 3. МОДУЛ: НОВ ОПИТ
elif menu == "📝 Нов Лабораторен Опит":
    st.header("📝 Нов Опит")
    with st.form("exp_form"):
        col1, col2 = st.columns(2)
        with col1:
            e_date = st.date_input("Дата", datetime.now())
            e_researcher = st.text_input("Изследовател", "Студент / Научен ръководител")
            cell_options = df_batt["Име на Папка/Батерия"].tolist() if not df_batt.empty else ["Общ опит"]
            e_battery = st.selectbox("Към папка", cell_options)
        with col2:
            e_title = st.text_input("Заглавие")
            e_params = st.text_input("Параметри", "25°C")
        e_why = st.text_area("🎯 ЗАЩО (Цел)", height=80)
        e_how = st.text_area("🛠️ КАКВО (Процедура)", height=100)
        e_chem = st.text_input("Формула (LaTeX)", "LiCoO2")
        if st.form_submit_button("💾 Запази опита"):
            new_e = pd.DataFrame([{"ID": datetime.now().strftime("%Y%m%d%H%M%S"), "Кога (Дата)": e_date.strftime("%Y-%m-%d"), "Име на Батерия/Клетка": e_battery, "Изследовател": e_researcher, "Заглавие": e_title, "Какво е направено": e_how, "Защо е направено (Цел)": e_why, "Органична формула (SMILES/LaTeX)": e_chem, "Параметри": e_params}])
            pd.concat([df_exp, new_e], ignore_index=True).to_csv(EXP_FILE, index=False, encoding='utf-8-sig')
            st.success("Опитът бе записан!")
            st.rerun()

# 4. МОДУЛ: АРХИВ
elif menu == "📚 Пълен Архив (Редакция & Изтриване)":
    st.header("📚 Архив")
    if not df_exp.empty:
        cell_filter = st.selectbox("Филтър по папка", ["Всички"] + df_exp["Име на Батерия/Клетка"].unique().tolist())
        filtered_df = df_exp if cell_filter == "Всички" else df_exp[df_exp["Име на Батерия/Клетка"] == cell_filter]
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📅 {row['Кога (Дата)']} | 🔋 {row['Име на Батерия/Клетка']} | 📌 {row['Заглавие']}"):
                st.write(f"**Изследовател:** {row['Изследовател']}")
                st.write(f"**🎯 ЗАЩО:** {row['Защо е направено (Цел)']}")
                st.write(f"**🛠️ КАКВО:** {row['Какво е направено']}")
                if st.button(f"❌ Изтрий опита", key=f"del_exp_{idx}"):
                    df_exp.drop(idx).to_csv(EXP_FILE, index=False, encoding='utf-8-sig')
                    st.rerun()

# 5. МОДУЛ: ГРАФИКИ
elif menu == "📊 Анализ & Графики":
    st.header("📊 Графики")
    col_x, col_y = st.columns(2)
    with col_x:
        x_values = st.text_input("Стойности X", "0, 20, 50, 80, 110, 140, 150")
    with col_y:
        y_values = st.text_input("Стойности Y", "4.2, 4.0, 3.8, 3.6, 3.4, 3.0, 2.5")
    if st.button("Генерирай Крива"):
        try:
            x = [float(i.strip()) for i in x_values.split(",")]
            y = [float(i.strip()) for i in y_values.split(",")]
            fig, ax = plt.subplots()
            ax.plot(x, y, marker='s', color='r')
            ax.grid(True)
            st.pyplot(fig)
        except Exception:
            st.error("Въведете числа, разделени със запетая!")
