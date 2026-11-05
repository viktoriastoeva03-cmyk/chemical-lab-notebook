import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.set_page_config(page_title="Електрохимия & Лабораторен Дневник", layout="wide")

st.title("🧪 Електрохимия & Лабораторен Дневник")
st.write("Проследяемост на опити (Какво, Защо, Кога), Органични структури, Канали на Абрин и Батерии")

# Файлове за локално съхранение на компютъра
EXP_FILE = "experiments_v2.csv"
BATTERIES_FILE = "batteries_v2.csv"
ABRIN_FILE = "abrin_channels.csv"

def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path, encoding='utf-8-sig')
        except Exception:
            return pd.read_csv(file_path, encoding='utf-8')
    return pd.DataFrame(columns=columns)

df_exp = load_data(EXP_FILE, ["ID", "Кога (Дата)", "Име на Батерия/Клетка", "Изследовател", "Заглавие", "Какво е направено", "Защо е направено (Цел)", "Органична формула (SMILES/LaTeX)", "Параметри"])
df_batt = load_data(BATTERIES_FILE, ["Име на Папка/Батерия", "Дата на сглобяване", "Партиден №", "Тип клетка / Състав", "Цел / Назначение"])
df_abrin = load_data(ABRIN_FILE, ["Канал", "Име на Клетка / Батерия", "Забележка", "Дата на поставяне"])

menu = st.sidebar.radio("📋 Модули", [
    "🔌 Абрин: Разпределение по Канали",
    "📁 Папки: Клетки / Батерии",
    "📝 Нов Лабораторен Опит",
    "📚 Пълен Архив (Редакция & Изтриване)",
    "📊 Анализ & Графики"
])

# 1. МОДУЛ: АБРИН (КАНАЛИ С ЦВЕТОВЕ И ИЗЧИСТВАНЕ)
if menu == "🔌 Абрин: Разпределение по Канали":
    st.header("🔌 Разпределение на клетките по канали в Абрин")
    st.write("Зелен цвят = Свободен канал | Червен цвят = Зает канал")

    abrin_dict = {}
    if not df_abrin.empty:
        for idx, row in df_abrin.iterrows():
            abrin_dict[str(row["Канал"])] = row

    st.subheader("📍 Текущо състояние на каналите")
    
    # Показваме каналите в 2 реда по 4 кутийки
    for row_idx in range(2):
        cols = st.columns(4)
        for col_idx in range(4):
            ch_num = row_idx * 4 + col_idx + 1
            ch_key = f"Канал {ch_num}"
            
            with cols[col_idx]:
                if ch_key in abrin_dict and str(abrin_dict[ch_key]["Име на Клетка / Батерия"]).strip() != "":
                    cell_info = abrin_dict[ch_key]
                    st.error(f"### 🔴 {ch_key}\n\n**ЗАЕТ от:**\n\n🔋 **{cell_info['Име на Клетка / Батерия']}**\n\n📅 {cell_info['Дата на поставяне']}\n\n⚙️ {cell_info['Забележка']}")
                    
                    # Бутон за премахване/освобождаване на канала
                    if st.button(f"🗑️ Освободи {ch_key}", key=f"clear_{ch_num}"):
                        df_abrin_updated = df_abrin[df_abrin["Канал"] != ch_key]
                        df_abrin_updated.to_csv(ABRIN_FILE, index=False, encoding='utf-8-sig')
                        st.success(f"{ch_key} беше освободен!")
                        st.rerun()
                else:
                    st.success(f"### 🟢 {ch_key}\n\n**Свободен**\n\n(Готов за поставяне на клетка)")

    st.markdown("---")
    st.subheader("⚙️ Поставяне на клетка в канал")
    with st.form("abrin_form"):
        col1, col2 = st.columns(2)
        with col1:
            channel_select = st.selectbox("Изберете Канал", [f"Канал {i}" for i in range(1, 9)])
            cell_options = df_batt["Име на Папка/Батерия"].tolist() if not df_batt.empty else ["Няма създадени клетки"]
            selected_cell = st.selectbox("Изберете Клетка/Батерия", cell_options)
        with col2:
            ch_notes = st.text_input("Параметри (Ток, Волтаж, Режим)", "0.1 mA, 2.8-4.2V")
            ch_date = st.date_input("Дата на пускане", datetime.now())
            
        submit_abrin = st.form_submit_button("Запази в канала")
        if submit_abrin:
            if selected_cell == "Няма създадени клетки":
                st.error("Първо създайте клетка от раздел 'Папки: Клетки / Батерии'!")
            else:
                df_abrin_clean = df_abrin[df_abrin["Канал"] != channel_select]
                new_ch = pd.DataFrame([{
                    "Канал": channel_select,
                    "Име на Клетка / Батерия": selected_cell,
                    "Забележка": ch_notes,
                    "Дата на поставяне": ch_date.strftime("%Y-%m-%d")
                }])
                df_abrin_updated = pd.concat([df_abrin_clean, new_ch], ignore_index=True)
                df_abrin_updated.to_csv(ABRIN_FILE, index=False, encoding='utf-8-sig')
                st.success(f"Клетка '{selected_cell}' е зачислена към {channel_select}!")
                st.rerun()

# 2. МОДУЛ: ПАПКИ И БАТЕРИИ
elif menu == "📁 Папки: Клетки / Батерии":
    st.header("📁 Папки (Клетки и Батерии)")
    
    with st.form("battery_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            b_name = st.text_input("Име на Клетката / Батерията", "Cell_NMC_01")
            b_date = st.date_input("Дата на сглобяване", datetime.now())
        with col2:
            b_num = st.text_input("Номер / Партиден №", "BATT-2026-001")
            b_type = st.text_input("Тип клетка / Активен материал", "Органичен катод")
        with col3:
            b_target = st.text_area("Цел / Назначение", "Тестване на нов електролит")
            
        submit_b = st.form_submit_button("📁 Създай Папка")
        
        if submit_b:
            new_b = pd.DataFrame([{
                "Име на Папка/Батерия": b_name,
                "Дата на сглобяване": b_date.strftime("%Y-%m-%d"),
                "Партиден №": b_num,
                "Тип клетка / Състав": b_type,
                "Цел / Назначение": b_target
            }])
            df_batt_updated = pd.concat([df_batt, new_b], ignore_index=True)
            df_batt_updated.to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
            st.success(f"Папката '{b_name}' бе създадена!")
            st.rerun()

    st.subheader("📚 Налични папки")
    if not df_batt.empty:
        for idx, row in df_batt.iterrows():
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.write(f"📁 **{row['Име на Папка/Батерия']}** | Партида: {row['Партиден №']} | Дата: {row['Дата на сглобяване']} | Състав: {row['Тип клетка / Състав']}")
            with col_del:
                if st.button("🗑️ Изтрий", key=f"del_batt_{idx}"):
                    df_batt_updated = df_batt.drop(idx)
                    df_batt_updated.to_csv(BATTERIES_FILE, index=False, encoding='utf-8-sig')
                    st.success("Папката е изтрита!")
                    st.rerun()

# 3. МОДУЛ: НОВ ОПИТ
elif menu == "📝 Нов Лабораторен Опит":
    st.header("📝 Записване на Нов Опит")
    
    with st.form("exp_form"):
        col1, col2 = st.columns(2)
        with col1:
            e_date = st.date_input("Кога (Дата)", datetime.now())
            e_researcher = st.text_input("Изследовател", "Студент / Научен ръководител")
            cell_options = df_batt["Име на Папка/Батерия"].tolist() if not df_batt.empty else ["Общ опит"]
            e_battery = st.selectbox("Към коя папка се записва?", cell_options)
        with col2:
            e_title = st.text_input("Заглавие на опита")
            e_params = st.text_input("Параметри (Температура, pH)", "25°C, 1 M LiPF6")
            
        e_why = st.text_area("🎯 ЗАЩО е направен опита (Цел / Хипотеза)", height=80)
        e_how = st.text_area("🛠️ КАКВО е направено (Процедура и наблюдения)", height=100)
        e_chem = st.text_input("Химична формула / Уравнение (LaTeX)", "H2SO4 + 2NaOH -> Na2SO4 + 2H2O")
        
        submit_exp = st.form_submit_button("💾 Запази опита")
        
        if submit_exp:
            exp_id = datetime.now().strftime("%Y%m%d%H%M%S")
            new_e = pd.DataFrame([{
                "ID": exp_id,
                "Кога (Дата)": e_date.strftime("%Y-%m-%d"),
                "Име на Батерия/Клетка": e_battery,
                "Изследовател": e_researcher,
                "Заглавие": e_title,
                "Какво е направено": e_how,
                "Защо е направено (Цел)": e_why,
                "Органична формула (SMILES/LaTeX)": e_chem,
                "Параметри": e_params
            }])
            df_exp_updated = pd.concat([df_exp, new_e], ignore_index=True)
            df_exp_updated.to_csv(EXP_FILE, index=False, encoding='utf-8-sig')
            st.success("Опитът е записан локално!")
            st.rerun()

# 4. МОДУЛ: ПЪЛЕН АРХИВ (ИЗЧИСТВАНЕ НА ГРЕШКИ)
elif menu == "📚 Пълен Архив (Редакция & Изтриване)":
    st.header("📚 Архив на опитите (С възможност за премахване)")
    
    if not df_exp.empty:
        cell_filter = st.selectbox("Филтър по папка", ["Всички"] + df_exp["Име на Батерия/Клетка"].unique().tolist())
        filtered_df = df_exp if cell_filter == "Всички" else df_exp[df_exp["Име на Батерия/Клетка"] == cell_filter]
        
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📅 {row['Кога (Дата)']} | 🔋 {row['Име на Батерия/Клетка']} | 📌 {row['Заглавие']}"):
                st.write(f"**Изследовател:** {row['Изследовател']}")
                st.write(f"**🎯 ЗАЩО:** {row['Защо е направено (Цел)']}")
                st.write(f"**🛠️ КАКВО:** {row['Какво е направено']}")
                st.write(f"**⚙️ Параметри:** {row['Параметри']}")
                if pd.notna(row['Органична формула (SMILES/LaTeX)']):
                    st.write("**🧪 Формула:**")
                    st.latex(row['Органична формула (SMILES/LaTeX)'])
                
                # Бутон за изтриване на грешен опит
                if st.button(f"❌ Изтрий този опит", key=f"del_exp_{idx}"):
                    df_exp_updated = df_exp.drop(idx)
                    df_exp_updated.to_csv(EXP_FILE, index=False, encoding='utf-8-sig')
                    st.success("Грешният опит беше премахнат от файла!")
                    st.rerun()
    else:
        st.warning("Няма намерени опити.")

# 5. МОДУЛ: ГРАФИКИ
elif menu == "📊 Анализ & Графики":
    st.header("📊 Чертане на Графики")
    
    col_x, col_y = st.columns(2)
    with col_x:
        x_label = st.text_input("Ос X", "Капацитет (mAh/g)")
        x_values = st.text_input("Стойности X", "0, 20, 50, 80, 110, 140, 150")
    with col_y:
        y_label = st.text_input("Ос Y", "Напрежение (V)")
        y_values = st.text_input("Стойности Y", "4.2, 4.0, 3.8, 3.6, 3.4, 3.0, 2.5")
        
    if st.button("Генерирай Крива"):
        try:
            x = [float(i.strip()) for i in x_values.split(",")]
            y = [float(i.strip()) for i in y_values.split(",")]
            fig, ax = plt.subplots()
            ax.plot(x, y, marker='s', color='r', linestyle='-')
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_title("Зарядна / Разрядна Крива")
            ax.grid(True)
            st.pyplot(fig)
        except Exception:
            st.error("Въведете числа, разделени със запетая!")
