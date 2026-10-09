import pandas as pd
from collections import defaultdict
from lunardate import LunarDate
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime, date, timedelta
import configparser
import calendar

def extract_birthdate(id_number):
    """
    从身份证号中提取出生日期，返回年份、月份和日期。
    支持15位和18位身份证号。
    """
    id_number = id_number.strip()
    if len(id_number) == 18:
        birth_str = id_number[6:14]  # YYYYMMDD
    elif len(id_number) == 15:
        birth_str = '19' + id_number[6:12]  # 转换为YYYYMMDD
    else:
        return None, None, None  # 无效的身份证号长度

    try:
        year = int(birth_str[0:4])
        month = int(birth_str[4:6])
        day = int(birth_str[6:8])
        return year, month, day
    except ValueError:
        return None, None, None  # 无效的日期


def load_festivals_from_config():
    """
    从 festivals.ini 配置文件中读取公历和农历节日数据。
    """
    config = configparser.ConfigParser()
    config.read('festivals.ini', encoding='utf-8')

    # 读取公历节日
    gregorian_holidays = {}
    if 'solar_festivals' in config:
        for key, value in config['solar_festivals'].items():
            month, day = map(int, key.split(','))
            gregorian_holidays[(month, day)] = value

    # 读取农历节日
    lunar_holidays = {}
    if 'lunar_festivals' in config:
        for key, value in config['lunar_festivals'].items():
            month, day = map(int, key.split(','))
            lunar_holidays[(month, day)] = value

    return gregorian_holidays, lunar_holidays


def get_gregorian_holidays():
    """
    获取公历节日。
    """
    gregorian_holidays, _ = load_festivals_from_config()
    return gregorian_holidays


def get_lunar_holidays():
    """
    获取农历节日。
    """
    _, lunar_holidays = load_festivals_from_config()
    return lunar_holidays


def convert_lunar_to_gregorian(lunar_year, lunar_month, lunar_day):
    """
    将农历日期转换为公历日期。
    """
    try:
        lunar_date = LunarDate(lunar_year, lunar_month, lunar_day)
        solar_date = lunar_date.toSolarDate()
        return solar_date
    except ValueError:
        return None  # 无效的农历日期


def get_nth_weekday(year, month, weekday, n):
    """
    获取指定年份、月份中第n个指定星期几的日期。

    参数:
    - year: 年份
    - month: 月份
    - weekday: 星期几（Monday=0, Sunday=6）
    - n: 第几个（1表示第一个，依此类推）

    返回:
    - date对象，如果不存在则返回None
    """
    c = calendar.Calendar()
    count = 0
    for day, wd in c.itermonthdays2(year, month):
        if day == 0:
            continue  # 跳过不属于该月的日期
        if wd == weekday:
            count += 1
            if count == n:
                return date(year, month, day)
    return None


def get_last_weekday(year, month, weekday):
    """
    获取指定年份、月份中最后一个指定星期几的日期。

    参数:
    - year: 年份
    - month: 月份
    - weekday: 星期几（Monday=0, Sunday=6）

    返回:
    - date对象，如果不存在则返回None
    """
    c = calendar.Calendar()
    weeks = list(c.monthdatescalendar(year, month))
    for week in reversed(weeks):
        day = week[weekday]
        if day.month == month:
            return day
    return None


def get_exam_date(year):
    """
    计算指定年份中6月最接近6月15日的周六和周日，作为中考日。
    """
    june_15 = date(year, 6, 15)
    weekday = june_15.weekday()

    # 计算最近的周六和周日
    if weekday < 5:  # 如果是周一到周五
        saturday = june_15 + timedelta(days=(5 - weekday))
    elif weekday > 5:  # 如果是周日
        saturday = june_15 - timedelta(days=(weekday - 5))
    else:  # 如果正好是周六
        saturday = june_15

    sunday = saturday + timedelta(days=1)  # 周日

    return {(saturday.month, saturday.day): "中考日_推算", (sunday.month, sunday.day): "中考日_推算"}

def add_research_weeks(year, holiday_dates):
    """
    将11月的第三周开始后的连续4个周一标记为“教科研月第i周”，i=1-4。
    """
    # 获取11月的第三个周一
    third_monday = get_nth_weekday(year, 11, 0, 3)  # Monday=0, 第三个
    if third_monday:
        for i in range(4):
            research_week = third_monday + timedelta(weeks=i)
            holiday_dates[(research_week.month, research_week.day)].append(f"教科研月第{i + 1}周")
            print(f"Added Research Week: ({research_week.month}, {research_week.day}) -> 教科研月第{i + 1}周")
    else:
        print("无法计算11月的第三个周一的日期。")

def add_cultivation_weeks(year, holiday_dates):
    """
    将9月份的前4周的每周二标记为“养成教育月第i周”，i=1-4。
    """
    # 获取9月的第一个周二
    first_tuesday = get_nth_weekday(year, 9, 1, 1)  # Tuesday=1, 第一个
    if first_tuesday:
        for i in range(4):
            cultivation_week = first_tuesday + timedelta(weeks=i)
            holiday_dates[(cultivation_week.month, cultivation_week.day)].append(f"养成教育月第{i + 1}周")
            print(f"Added Cultivation Week: ({cultivation_week.month}, {cultivation_week.day}) -> 养成教育月第{i + 1}周")
    else:
        print("无法计算9月的第一个周二的日期。")

def add_assessment_week(year, holiday_dates):
    """
    将11月的最后一个周二标记为“大课间操评估周”。
    """
    last_monday = get_last_weekday(year, 11, 1)  # Tuesday=1
    if last_monday:
        holiday_dates[(last_monday.month, last_monday.day)].append("大课间操评估周")
        print(f"Added Assessment Week: ({last_monday.month}, {last_monday.day}) -> 大课间操评估周")
    else:
        print("无法计算11月的最后一个周一的日期。")

def add_health_test_week(year, holiday_dates):
    """
    将9月的最后一个周二标记为“健康测试周”。
    """
    last_tuesday = get_last_weekday(year, 9, 1)  # Tuesday=1
    if last_tuesday:
        holiday_dates[(last_tuesday.month, last_tuesday.day)].append("健康测试周")
        print(f"Added Health Test Week: ({last_tuesday.month}, {last_tuesday.day}) -> 健康测试周")
    else:
        print("无法计算9月的最后一个周二的日期。")

def add_learning_week(year, holiday_dates):
    """
    将11月的第三个周二标记为“学会学习周”。
    """
    third_tuesday = get_nth_weekday(year, 11, 1, 3)  # Tuesday=1, 第三个
    if third_tuesday:
        holiday_dates[(third_tuesday.month, third_tuesday.day)].append("学会学习周")
        print(f"Added Learning Week: ({third_tuesday.month}, {third_tuesday.day}) -> 学会学习周")
    else:
        print("无法计算11月的第三个周二的日期。")

def add_facility_check_day(year, holiday_dates):
    """
    将12月的第二个周四标记为“教辅各室检查日”。
    """
    second_thursday = get_nth_weekday(year, 12, 3, 2)  # Thursday=3, 第二个
    if second_thursday:
        holiday_dates[(second_thursday.month, second_thursday.day)].append("教辅各室检查日")
        print(f"Added Facility Check Day: ({second_thursday.month}, {second_thursday.day}) -> 教辅各室检查日")
    else:
        print("无法计算12月的第二个周四的日期。")

def add_teaching_routine_month(year, holiday_dates):
    """
    将9月的前4个周二标记为“教学常规月第i周”，i=1-4。
    """
    # 获取9月的第一个周一
    first_tuesday = get_nth_weekday(year, 9, 0, 1)  # Monday=0, 第一个
    if first_tuesday:
        for i in range(4):
            routine_week = first_tuesday + timedelta(weeks=i)
            holiday_dates[(routine_week.month, routine_week.day)].append(f"教学常规月第{i + 1}周")
            print(f"Added Teaching Routine Week: ({routine_week.month}, {routine_week.day}) -> 教学常规月第{i + 1}周")
    else:
        print("无法计算9月的第一个周二的日期。")


def add_competition_week(year, holiday_dates):
    """
    将4月的第四个周二标记为“学科竞赛周”。
    """
    fourth_tuesday = get_nth_weekday(year, 4, 1, 4)  # Tuesday=1, 第四个
    if fourth_tuesday:
        holiday_dates[(fourth_tuesday.month, fourth_tuesday.day)].append("学科竞赛周")
        print(f"Added Competition Week: ({fourth_tuesday.month}, {fourth_tuesday.day}) -> 学科竞赛周")
    else:
        print("无法计算4月的第四个周二的日期。")


def generate_config(selected_year):
    """
    生成config.ini文件，包含所有节日和对应的生日姓名。
    仅包含公历selected_year年内的节日。
    """
    print(f"Generating config for year: {selected_year}")
    excel_file = '身份证号.xlsx'

    # 检查文件是否存在
    if not os.path.isfile(excel_file):
        try:
            # 创建一个空的DataFrame，包含必要的列
            empty_df = pd.DataFrame(columns=['姓名', '身份证号'])
            empty_df.to_excel(excel_file, index=False)
            messagebox.showinfo("文件创建", f"文件 '{excel_file}' 未找到，已在当前目录创建一个空的 '{excel_file}' 文件。")
            print(f"Empty '{excel_file}' created.")
            # 询问用户是否继续生成config.ini
            continue_choice = messagebox.askyesno("继续生成", "是否继续生成 config.ini 文件？")
            if continue_choice:
                print("用户选择继续生成 config.ini 文件。")
                # 继续执行函数，即不返回，而是继续到后续逻辑
            else:
                print("用户选择退出程序。")
                return
        except Exception as e:
            messagebox.showerror("创建错误", f"无法创建空的 '{excel_file}' 文件: {e}")
            print(f"Error creating empty '{excel_file}': {e}")

    # 读取Excel文件
    try:
        df = pd.read_excel(excel_file, dtype={'姓名': str, '身份证号': str})
        print("Excel file read successfully.")
    except Exception as e:
        messagebox.showerror("读取错误", f"读取Excel文件时发生错误: {e}")
        print(f"Error reading Excel file: {e}")
        return

    # 检查必要的列
    if '姓名' not in df.columns or '身份证号' not in df.columns:
        messagebox.showerror("缺少列", "Excel文件中缺少 '姓名' 或 '身份证号' 列。")
        print("Excel file missing required columns.")
        return

    # 创建新的 config.ini 文件之前，检查是否已有存在的文件
    config_file = 'config.ini'
    if os.path.exists(config_file):
        i = 1
        while True:
            backup_file = f'config_{i}.ini'
            if not os.path.exists(backup_file):
                os.rename(config_file, backup_file)
                print(f"Existing config.ini renamed to {backup_file}")
                break
            i += 1

    # 提取所有生日信息
    birthdays = defaultdict(list)  # (month, day) -> [names]

    for index, row in df.iterrows():
        name = row['姓名']
        id_number = row['身份证号']

        if pd.isna(name) or pd.isna(id_number):
            continue  # 跳过缺失数据

        id_number = str(id_number).strip()

        # 提取出生日期
        year, month, day = extract_birthdate(id_number)
        if year is None or month is None or day is None:
            print("发现格式无效的身份证号码，已跳过该行。")
            continue

        birthdays[(month, day)].append(name)
        print("已读取一条生日记录。")

    # 定义所有公历节日
    gregorian_holidays = get_gregorian_holidays()
    print("Gregorian holidays defined.")

    # 定义所有农历节日
    lunar_holidays = get_lunar_holidays()
    print("Lunar holidays defined.")

    # 定义所选公历年的开始和结束日期
    start_date = date(selected_year, 1, 1)
    end_date = date(selected_year, 12, 31)

    relevant_lunar_years = [selected_year -1, selected_year]

    # 收集落在所选公历年内的节日
    holiday_dates = defaultdict(list)  # (month, day) -> [holiday_names]

    # 添加公历节日
    for (month, day), holiday_name in gregorian_holidays.items():
        holiday_dates[(month, day)].append(holiday_name)
        print("已合并一条公历节日记录。")

    # 计算并添加母亲节和父亲节
    mothers_day = get_nth_weekday(selected_year, 5, 6, 2)  # 第二个星期日，Sunday=6
    fathers_day = get_nth_weekday(selected_year, 6, 6, 3)  # 第三个星期日，Sunday=6

    if mothers_day:
        holiday_dates[(mothers_day.month, mothers_day.day)].append("母亲节")
        print(f"Added Mother's Day: ({mothers_day.month}, {mothers_day.day}) -> 母亲节")
    else:
        print("无法计算母亲节的日期。")

    if fathers_day:
        holiday_dates[(fathers_day.month, fathers_day.day)].append("父亲节")
        print(f"Added Father's Day: ({fathers_day.month}, {fathers_day.day}) -> 父亲节")
    else:
        print("无法计算父亲节的日期。")

    # 计算并添加感恩节
    thanksgiving_day = get_nth_weekday(selected_year, 11, 3, 4)  # 第四个星期四，Thursday=3
    if thanksgiving_day:
        holiday_dates[(thanksgiving_day.month, thanksgiving_day.day)].append("感恩节")
        print(f"Added Thanksgiving Day: ({thanksgiving_day.month}, {thanksgiving_day.day}) -> 感恩节")
    else:
        print("无法计算感恩节的日期。")

    # ---------------------- 添加推普周 ----------------------
    # 计算9月第三个星期一
    push_mandarin_start = get_nth_weekday(selected_year, 9, 0, 3)  # Monday=0, 第三个
    if push_mandarin_start:
        print(f"推普周开始日期: {push_mandarin_start}")
        # 仅将推普周的开始日期添加到节日日期
        key = (push_mandarin_start.month, push_mandarin_start.day)
        holiday_dates[key].append("推普周")
        print(f"Added 推普周: ({key[0]}, {key[1]}) -> 推普周")
    else:
        print("无法计算推普周的开始日期。")
    # --------------------------------------------------------

    # ---------------------- 添加安全教育日 ----------------------
    # 计算3月最后一个星期一
    safety_education_day = get_last_weekday(selected_year, 3, 0)  # Monday=0
    if safety_education_day:
        print(f"安全教育日日期: {safety_education_day}")
        # 将安全教育日添加到节日日期
        key = (safety_education_day.month, safety_education_day.day)
        holiday_dates[key].append("安全教育周")
        print(f"Added 安全教育周: ({key[0]}, {key[1]}) -> 安全教育周")
    else:
        print("无法计算安全教育日的日期。")
    # --------------------------------------------------------

    # ---------------------- 添加数学周 ----------------------
    # 计算3月第二个星期一
    math_week = get_nth_weekday(selected_year, 3, 0, 2)  # Monday=0, 第二个
    if math_week:
        print(f"数学周日期: {math_week}")
        # 将数学周添加到节日日期
        key = (math_week.month, math_week.day)
        holiday_dates[key].append("数学周")
        print(f"Added 数学周: ({key[0]}, {key[1]}) -> 数学周")
    else:
        print("无法计算数学周的日期。")
    # --------------------------------------------------------

    # ---------------------- 添加英语周 ----------------------
    # 计算10月第二个星期一
    english_week = get_nth_weekday(selected_year, 10, 0, 2)  # Monday=0, 第二个
    if english_week:
        print(f"英语周日期: {english_week}")
        # 将英语周添加到节日日期
        key = (english_week.month, english_week.day)
        holiday_dates[key].append("英语周")
        print(f"Added 英语周: ({key[0]}, {key[1]}) -> 英语周")
    else:
        print("无法计算英语周的日期。")
    # --------------------------------------------------------

    # ---------------------- 添加中考日 ----------------------
    # 获取6月最接近15日的周六和周日作为中考日
    exam_dates = get_exam_date(selected_year)
    for (month, day), label in exam_dates.items():
        holiday_dates[(month, day)].append(label)
        print(f"Added Exam Day: ({month}, {day}) -> {label}")
    # --------------------------------------------------------

    # ---------------------- 添加教科研月 ----------------------
    add_research_weeks(selected_year, holiday_dates)
    # --------------------------------------------------------


    # ---------------------- 添加养成教育月 ----------------------
    add_cultivation_weeks(selected_year, holiday_dates)
    # --------------------------------------------------------

    # ---------------------- 添加大课间操评估周 ----------------------
    add_assessment_week(selected_year, holiday_dates)
    # ------------

    # ---------------------- 添加健康测试周 ----------------------
    add_health_test_week(selected_year, holiday_dates)
    # --------------------------------------------------------

    # ---------------------- 添加学会学习周 ----------------------
    add_learning_week(selected_year, holiday_dates)
    # --------------------------------------------------------

    # ---------------------- 添加教辅各室检查日 ----------------------
    add_facility_check_day(selected_year, holiday_dates)
    # --------------------------------------------------------

    # ---------------------- 添加教学常规月 ----------------------
    add_teaching_routine_month(selected_year, holiday_dates)
    # --------------------------------------------------------

    # ---------------------- 添加学科竞赛周 ----------------------
    add_competition_week(selected_year, holiday_dates)
    # --------------------------------------------------------

    # 遍历相关农历年份并转换节日
    for lunar_year in relevant_lunar_years:
        for (lunar_month, lunar_day), holiday_name in lunar_holidays.items():
            solar_date = convert_lunar_to_gregorian(lunar_year, lunar_month, lunar_day)
            if solar_date and start_date <= solar_date <= end_date:
                holiday_dates[(solar_date.month, solar_date.day)].append(holiday_name)
                print("已合并一条农历节日记录。")

    # 手动添加除夕
    # 除夕是农历年的最后一天，可以通过找农历年最后一天来确定
    for lunar_year in relevant_lunar_years:
        try:
            # 假设农历年有30天
            last_day = 30
            lunar_date = LunarDate(lunar_year, 12, last_day)
            solar_date = lunar_date.toSolarDate()
            if solar_date.year == selected_year:
                holiday_dates[(solar_date.month, solar_date.day)].append("除夕")
                print(f"Added Lunar holiday: ({solar_date.month}, {solar_date.day}) -> 除夕 (农历 {lunar_year}年12月{last_day}日)")
        except ValueError:
            # 如果农历12月30日不存在，则是29日
            try:
                last_day = 29
                lunar_date = LunarDate(lunar_year, 12, last_day)
                solar_date = lunar_date.toSolarDate()
                if solar_date.year == selected_year:
                    holiday_dates[(solar_date.month, solar_date.day)].append("除夕")
                    print(f"Added Lunar holiday: ({solar_date.month}, {solar_date.day}) -> 除夕 (农历 {lunar_year}年12月{last_day}日)")
            except ValueError:
                print(f"农历 {lunar_year}年12月29日不存在，无法添加除夕。")

    # 过滤掉落在下一公历年的农历节日（理论上已经通过日期范围筛选）
    # 但为了确保安全，可以再次筛选
    final_holiday_dates = defaultdict(list)
    for (month, day), names in holiday_dates.items():
        try:
            solar_date = date(selected_year, month, day)
            final_holiday_dates[(month, day)].extend(names)
            print("已合并一条日期记录。")
        except ValueError:
            print(f"无效的日期 ({month}, {day})，已跳过。")
            continue

    # 合并生日信息到节日日期
    for (month, day), names in birthdays.items():
        if (month, day) in final_holiday_dates:
            final_holiday_dates[(month, day)].extend(names)
            print("已将生日记录合并到已有日期。")
        else:
            final_holiday_dates[(month, day)].extend(names)
            print("已新增生日日期记录。")

    # 按月份和日期排序
    sorted_holiday_dates = sorted(final_holiday_dates.items(), key=lambda x: (x[0][0], x[0][1]))
    print("Holiday dates sorted.")

    # 生成config.ini内容
    config_lines = ["[birthdays]\n"]
    for (month, day), items in sorted_holiday_dates:
        # 定义所有农历节日名称
        lunar_festivals = set([
            "春节", "元宵节", "龙抬头", "上巳节",
            "端午节", "七夕节", "中元节", "中秋节",
            "重阳节", "下元节", "腊八节", "小年",
            "除夕"
        ])
        # 定义所有公历节日名称
        gregorian_festivals = set(gregorian_holidays.values()).union({
            "母亲节", "父亲节", "感恩节", "推普周",
            "安全教育日", "数学周", "英语周"
        })

        # 分离节日名称和生日姓名
        holiday_names = [item for item in items if item in lunar_festivals or item in gregorian_festivals]
        birthday_names = [item for item in items if item not in holiday_names]

        # 合并节日和生日，去除重复
        line_content = ", ".join(holiday_names + birthday_names)
        config_lines.append(f"({month}, {day}): {line_content}\n")
        print("已写入一条日期配置。")

    # 写入config.ini文件
    try:
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.writelines(config_lines)
        messagebox.showinfo("成功", "config.ini 文件已成功生成。")
        print("config.ini generated successfully.")
    except Exception as e:
        messagebox.showerror("写入错误", f"写入config.ini文件时发生错误: {e}")
        print(f"Error writing config.ini: {e}")


def on_generate():
    """
    事件处理器，当用户点击生成按钮时调用。
    """
    year_str = year_combobox.get()
    try:
        selected_year = int(year_str)
        if not (1900 <= selected_year <= 2100):
            raise ValueError
        print(f"Selected year: {selected_year}")
    except ValueError:
        messagebox.showerror("输入错误", "请选择或输入有效的年份（例如：2025）。")
        print("Invalid year input.")
        return

    generate_config(selected_year)


def create_gui():
    """
    创建Tkinter GUI界面。
    """
    root = tk.Tk()
    root.title("生日与节日配置生成器 v0.18")
    root.geometry("450x500")  # 增加窗口宽度和高度以获得更好的布局
    root.resizable(False, False)

    # 设置样式
    style = ttk.Style(root)
    style.theme_use('clam')  # 使用clam主题，您也可以尝试其他主题如 'default', 'alt', 'classic', 'vista', 'xpnative'

    # 添加标题标签
    title_label = ttk.Label(root, text="生日与节日配置生成器", font=("Helvetica", 18, "bold"))
    title_label.pack(pady=20)

    # 说明标签
    config_label = ttk.Label(
        root,
        text="添加或修改节日名称请在festivals.ini中配置。",
        font=("Helvetica", 13),
        foreground="red"
    )
    config_label.pack(pady=10)

    # 创建框架用于年份输入和下拉菜单
    input_frame = ttk.Frame(root, padding=20)
    input_frame.pack(pady=10, fill='x')

    year_label = ttk.Label(input_frame, text="选择年份:", font=("Helvetica", 12))
    year_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

    # 创建年份下拉菜单（Combobox）
    current_year = datetime.now().year
    years = list(range(1900, 2101))  # 年份范围从1900到2100
    global year_combobox
    year_combobox = ttk.Combobox(input_frame, values=years, state="readonly", width=10, font=("Helvetica", 12))
    year_combobox.set(str(current_year))  # 设置默认值为当前年份
    year_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # 可选：允许用户输入其他年份
    # 如果希望用户既可以选择下拉菜单中的年份，也可以手动输入其他年份，可以设置state为 "normal"
    # year_combobox.configure(state="normal")

    # 创建生成和退出按钮的框架
    button_frame = ttk.Frame(root, padding=20)
    button_frame.pack(pady=20)

    # 创建生成按钮
    generate_button = ttk.Button(button_frame, text="生成 config.ini", command=on_generate, width=20)
    generate_button.grid(row=0, column=0, padx=10, pady=10)

    # 创建退出按钮
    exit_button = ttk.Button(button_frame, text="退出", command=root.destroy, width=20)
    exit_button.grid(row=0, column=1, padx=10, pady=10)


    # 添加说明标签
    info_label = ttk.Label(root, text="请从下拉菜单中选择年份，或手动输入一个年份（1900-2100）。", font=("Helvetica", 10), foreground="blue")
    info_label.pack(pady=12)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
