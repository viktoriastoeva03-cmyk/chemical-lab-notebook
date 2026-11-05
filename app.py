import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.set_page_config(page_title="Разширен Химичен & Клетъчен Дневник", layout="wide")

st.title("🧪 Лабораторен Софтуер: Химия & Електрохимия")
st.write("Проследяемост на опити (Какво, Защо, Кога), Органични структури, Канали на Абрин и Батерии")

# Файлове за съхранение на данни
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

df_exp = load_data(EXP_FILE, ["Кога (Дата)", "Име на Батерия/Клетка", "Изследовател", "Заглавие", "Какво е направено", "Защо е направено (Цел)", "Органична формула (SMILES/LaTeX)", "Параметри"])
df_batt = load_data(BATTERIES_FILE, ["Име на Папка/Батерия", "Дата на сглобяване", "Партиден №", "Тип клетка / Състав", "Цел / Назначение"])
df_abrin = load_data(ABRIN_FILE, ["Канал", "Име на Клетка / Батерия", "Забележка", "Дата на поставяне"])

menu = st.sidebar.radio("📋 Модули", [
    "📁 Папки: Клетки / Батерии",
    "🔌 Абрин: Разпределение по Канали",
    "📝 Нов Лабораторен Опит",
    "📚 Пълен Архив (Какво, Защо, Кога)",
    "📊 Анализ & Графики"
])

# 1. МОДУЛ: ПАПКИ И БАТЕРИИ
if menu == "📁 Папки: Клетки / Батерии":
    st.header("📁 Организиране на Папки (Клетки и Батерии)")
    st.write("Създайте папка за всяка конкретна клетка/батерия с нейния уникален номер и състав.")
    
    with st.form("battery_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            b_name = st.text_input("Име на Клетката / Батерията", "напр. Cell_NMC_01")
            b_date = st.date_input("Дата на сглобяване", datetime.now())
        with col2:
            b_num = st.text_input("Номер / Партиден №", "напр. BATT-2026-004")
            b_type = st.text_input("Тип клетка / Активен материал", "напр. Органичен катод / Литиева")
        with col3:
            b_target = st.text_area("Защо е направена (Цел)", "Тестване на нов електролит...")
            
        submit_b = st.form_submit_button("📁 Създай Папка / Клетка")
        
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
            st.success(f"Папката за клетка '{b_name}' беше създадена успешно!")
            st.rerun()

    st.subheader("📚 Списък на наличните папки с клетки")
    if not df_batt.empty:
        st.dataframe(df_batt, use_container_width=True)

# 2. МОДУЛ: АБРИН (КАНАЛИ)
elif menu == "🔌 Абрин: Разпределение по Канали":
    st.header("🔌 Разпределение на клетките по канали в Абрин")
    st.write("Следете коя клетка на кой канал е поставена за измерване.")

    # Мониторинг на каналите (Табло с кутийки)
    st.subheader("📍 Текущо състояние на каналите")
    cols = st.columns(4)
    abrin_dict = dict(zip(df_abrin["Канал"].astype(str), df_abrin["Име на Клетка / Батерия"])) if not df_abrin.empty else {}
    
    for i in range(1, 9):
        ch_key = f"Канал {i}"
        cell_in_ch = abrin_dict.get(ch_key, "Празен")
        with cols[(i-1) % 4]:
            if cell_in_ch != "Празен":
                st.success(f"**{ch_key}**\n\n🔋 {cell_in_ch}")
            else:
                st.info(f"**{ch_key}**\n\n⚪ Свободен")

    st.markdown("---")
    st.subheader("⚙️ Записване / Промяна на клетка в канал")
    with st.form("abrin_form"):
        col1, col2 = st.columns(2)
        with col1:
            channel_select = st.selectbox("Изберете Канал", [f"Канал {i}" for i in range(1, 9)])
            cell_options = df_batt["Име на Папка/Батерия"].tolist() if not df_batt.empty else ["Няма създадени клетки"]
            selected_cell = st.selectbox("Изберете Клетка/Батерия от папките", cell_options)
        with col2:
            ch_notes = st.text_input("Параметри на канала (напр. Ток: 0.1 mA, Волтаж: 2.8-4.2V)")
            ch_date = st.date_input("Дата на пускане", datetime.now())
            
        submit_abrin = st.form_submit_button("Запази в канала")
        if submit_abrin:
            # Премахваме стария запис за този канал, ако има такъв
            df_abrin_clean = df_abrin[df_abrin["Канал"] != channel_select]
            new_ch = pd.DataFrame([{
                "Канал": channel_select,
                "Име на Клетка / Батерия": selected_cell,
                "Забележка": ch_notes,
                "Дата на поставяне": ch_date.strftime("%Y-%m-%d")
            }])
            df_abrin_updated = pd.concat([df_abrin_clean, new_ch], ignore_index=True)
            df_abrin_updated.to_csv(ABRIN_FILE, index=False, encoding='utf-8-sig')
            st.success(f"Клетка {selected_cell} е зачислена към {channel_select}!")
            st.rerun()

# 3. МОДУЛ: НОВ ОПИТ
elif menu == "📝 Нов Лабораторен Опит":
    st.header("📝 Добавяне на опит към конкретна Клетка / Батерия")
    
    with st.form("exp_form"):
        col1, col2 = st.columns(2)
        with col1:
            e_date = st.date_input("Кога е направен опита (Дата)", datetime.now())
            e_researcher = st.text_input("Изследовател", "Студент / Научен ръководител")
            cell_options = df_batt["Име на Папка/Батерия"].tolist() if not df_batt.empty else ["Общ опит"]
            e_battery = st.selectbox("Към коя папка/клетка се записва?", cell_options)
        with col2:
            e_title = st.text_input("Заглавие на опита")
            e_params = st.text_input("Параметри (Температура, pH, Цикли)", "25°C, 1 M LiPF6")
            
        e_why = st.text_area("🎯 ЗАЩО е направен опита (Цел / Хипотеза)", height=80)
        e_how = st.text_area("🛠️ КАКВО е направено (Стъпки, процедура, наблюдения)", height=120)
        
        st.subheader("🧪 Органични формули и уравнения")
        st.info("💡 Можете да въведете формулата като LaTeX текст (напр. $C_6H_{12}O_6$) или структура.")
        e_chem = st.text_input("Химична формула / Уравнение", "C6H12O6 -> 2 C2H5OH + 2 CO2")
        
        submit_exp = st.form_submit_button("💾 Запази опита в дневника")
        
        if submit_exp:
            new_e = pd.DataFrame([{
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
            st.success("Опитът беше записан успешно!")
            st.rerun()

# 4. МОДУЛ: ПЪЛЕН АРХИВ
elif menu == "📚 Пълен Архив (Какво, Защо, Кога)":
    st.header("📚 Пълна история на опитите по клетки")
    
    if not df_exp.empty:
        # Филтър по клетка
        cell_filter = st.selectbox("Филтрирай по Папка / Клетка", ["Всички"] + df_exp["Име на Батерия/Клетка"].unique().tolist())
        
        filtered_df = df_exp if cell_filter == "Всички" else df_exp[df_exp["Име на Батерия/Клетка"] == cell_filter]
        
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📅 {row['Кога (Дата)']} | 🔋 {row['Име на Батерия/Клетка']} | 📌 {row['Заглавие']}"):
                st.write(f"**Изследовател:** {row['Изследовател']}")
                st.write(f"**🎯 ЗАЩО (Цел):** {row['Защо е направено (Цел)']}")
                st.write(f"**🛠️ КАКВО (Процедура):** {row['Какво е направено']}")
                st.write(f"**⚙️ Параметри:** {row['Параметри']}")
                if pd.notna(row['Органична формула (SMILES/LaTeX)']):
                    st.write("**🧪 Формула / Реакция:**")
                    st.latex(row['Органична формула (SMILES/LaTeX)'])
    else:
        st.warning("Все още няма записани опити.")

# 5. МОДУЛ: ГРАФИКИ
elif menu == "📊 Анализ & Графики":
    st.header("📊 Аналитични Криви на Клетките")
    st.write("Чертане на разрядни/зарядни криви или кинетика.")
    
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
            ax.plot(x, y, marker='s', color='b', linestyle='-')
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_title("Волтаперна / Зарядна крива")
            ax.grid(True)
            st.pyplot(fig)
        except Exception:
            st.error("Уверете се, че стойностите са числа, разделени със запетая!")