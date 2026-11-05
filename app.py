import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Лабораторен Дневник", layout="wide")

st.title("🧪 Електрохимия & Лабораторен Дневник")

FILES_DIR = "uploaded_files"
os.makedirs(FILES_DIR, exist_ok=True)

EXP_FILE = "experiments_v2.csv"
BATTERIES_FILE = "batteries_v2.csv"
ABRIN_FILE = "abrin_channels.csv"

# --- БЛОК ЗА АВТОМАТИЧНА СИНХРОНИЗАЦИЯ С GITHUB ---
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Облачна синхронизация")

if st.sidebar.button("🔄 Синхронизирай данните с 1 клик"):
    try:
        import git
        repo = git.Repo(os.getcwd())
        # Добавяне на променените CSV файлове и качения архив
        repo.index.add([EXP_FILE, BATTERIES_FILE, ABRIN_FILE])
        for root, dirs, files in os.walk(FILES_DIR):
            for f in files:
                repo.index.add(os.path.join(root, f))
                
        repo.index.commit("Auto-sync laboratory data from local laptop")
        origin = repo.remote(name='origin')
        origin.push()
        st.sidebar.success("✅ Успешно синхронизирано! Сайтът в интернет се обновява...")
    except Exception as e:
        st.sidebar.error(f"Грешка при синхронизация: {e}\n(Уверете се, че имате интернет връзка)")
# ---------------------------------------------------

def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except Exception:
            df = pd.read_csv(file_path, encoding='utf-8')
        return df.dropna(how='all').fillna("")
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

# 1. МОДУЛ: ПАПКИ И БАТЕРИИ
if menu == "📁 Папки: Клетки / Батерии & Сортиране":
    st.header("📁 Батерии & Клетки")
    tab1, tab2 = st.tabs(["➕ Ръчно добавяне", "📂 Масово качване (до 100 CSV/Excel файла)"])
    
    with tab1:
        with st.form("battery_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                b_name = st.text_input("Име на Клетката", "Cell_Li_NMC_01")
                b_date = st.date_input("Дата на сглобяване", pd.Timestamp.now())
            with col2:
                b_num = st.text_input("Партиден №", "BATT-2026-001")
                b_type = st.text_input("Материал / Състав", "Li-ion / NMC / Графит")
            with col3:
                b_target = st.text_area("Цел", "Тест при висок ток")
                
            if st.form_submit_button("📁 Запази клетка"):
                new_b = pd.DataFrame([{
                    "Име на Папка/Батерия": b_name,
                    "Дата на сглобяване": b_date.strftime("%Y-%m-%d"),
                    "Партиден №": b_num,
                    "Тип клетка / Състав": b_type,
                    "Цел / Назначение": b_target,
                    "Оригинален Файл": ""
                }])
                pd.concat([df_batt, new_b], ignore_index=True).to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                st.success(f"Клетката '{b_name}' е запазена локално!")
                st.rerun()

    with tab2:
        st.subheader("📥 Качване на файлове")
        uploaded_files = st.file_uploader("Изберете файлове (CSV/XLSX)", type=["csv", "xlsx"], accept_multiple_files=True)
        if uploaded_files and st.button("🚀 Добави всички качени файлове"):
            new_entries = []
            for file in uploaded_files:
                try:
                    base_name = os.path.splitext(file.name)[0]
                    saved_path = os.path.join(FILES_DIR, file.name)
                    with open(saved_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    new_entries.append({
                        "Име на Папка/Батерия": base_name,
                        "Дата на сглобяване": pd.Timestamp.now().strftime("%Y-%m-%d"),
                        "Партиден №": "OFFLINE-DATA",
                        "Тип клетка / Състав": base_name,
                        "Цел / Назначение": f"Файл: {file.name}",
                        "Оригинален Файл": file.name
                    })
                except Exception as e:
                    st.warning(f"Грешка с {file.name}: {e}")
            
            if new_entries:
                imported_df = pd.DataFrame(new_entries)
                pd.concat([df_batt, imported_df], ignore_index=True).drop_duplicates(subset=["Име на Папка/Батерия"]).to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                st.success("Успешно качени и запазени!")
                st.rerun()

    st.markdown("---")
    st.subheader("🔍 Архив на клетките")
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
            filtered_batt = filtered_batt[filtered_batt["Тип клетка / Състав"].astype(str).str.contains(search_mat, case=False, na=False)]

        for idx, row in filtered_batt.iterrows():
            file_name = str(row.get('Оригинален Файл', '')).strip()
            col_info, col_file, col_del = st.columns([5, 2, 1])
            with col_info:
                st.markdown(f"🔋 **{row['Име на Папка/Батерия']}** | 🧪 **{row['Химия (Li/Na)']}** | 📅 **{row['Дата на сглобяване']}** | ⚙️ **Състав:** {row['Тип клетка / Състав']}")
            with col_file:
                file_path = os.path.join(FILES_DIR, file_name) if file_name else ""
                if file_name and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(label="📥 Свали Excel", data=f, file_name=file_name, key=f"dl_{idx}")
                else:
                    st.caption("Няма файл")
            with col_del:
                if st.button("🗑️ Изтрий", key=f"del_cell_{idx}"):
                    df_batt.drop(idx).to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                    st.rerun()
    else:
        st.info("Все още няма качени или създадени клетки.")

# 2. МОДУЛ: АБРИН
elif menu == "🔌 Абрин: Разпределение по Канали":
    st.header("🔌 Канали в Абрин")
    abrin_dict = {str(row["Канал"]): row for idx, row in df_abrin.iterrows()} if not df_abrin.empty else {}
    for row_idx in range(2):
        cols = st.columns(4)
        for col_idx in range(4):
            ch_num = row_idx * 4 + col_idx + 1
            ch_key = f"Канал {ch_num}"
            with cols[col_idx]:
                if ch_key in abrin_dict and str(abrin_dict[ch_key]["Име на Клетка / Батерия"]).strip() != "":
                    cell_info = abrin_dict[ch_key]
                    st.error(f"### 🔴 {ch_key}\n\n🔋 **{cell_info['Име на Клетка / Батерия']}**")
                    if st.button(f"🗑️ Освободи", key=f"clear_{ch_num}"):
                        df_abrin[df_abrin["Канал"] != ch_key].to_csv(ABRIN_FILE, index=False, encoding='utf-8-sig')
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
            ch_date = st.date_input("Дата", pd.Timestamp.now())
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
            e_date = st.date_input("Дата", pd.Timestamp.now())
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
            new_e = pd.DataFrame([{"ID": pd.Timestamp.now().strftime("%Y%m%d%H%M%S"), "Кога (Дата)": e_date.strftime("%Y-%m-%d"), "Име на Батерия/Клетка": e_battery, "Изследовател": e_researcher, "Заглавие": e_title, "Какво е направено": e_how, "Защо е направено (Цел)": e_why, "Органична формула (SMILES/LaTeX)": e_chem, "Параметри": e_params}])
            pd.concat([df_exp, new_e], ignore_index=True).to_csv(EXP_FILE, index=False, encoding='utf-8-sig')
            st.success("Опитът бе записан локално!")
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
