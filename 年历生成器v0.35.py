import pandas as pd
import calendar
from skyfield.api import load
from skyfield import almanac
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import configparser
import ast
import os
from lunarcalendar import Converter, Solar
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.worksheet.page import PageMargins
import numpy as np
import math  # 引入math模块用于向上取整

# 定义24节气名称及对应黄经（度）
SOLAR_TERMS = [
    "立春", "雨水", "惊蛰", "春分",
    "清明", "谷雨", "立夏", "小满",
    "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪",
    "大雪", "冬至", "小寒", "大寒"
]

SOLAR_TERMS_LONGITUDES = [
    315, 330, 345, 0,
    15, 30, 45, 60,
    75, 90, 105, 120,
    135, 150, 165, 180,
    195, 210, 225, 240,
    255, 270, 285, 300
]

class SolarTermsFunction:
    # 必须作为类属性存在
    step_days = 1

    def __init__(self, eph, solar_terms_longitudes):
        self.eph = eph
        self.earth = eph['earth']
        self.sun = eph['sun']
        self.solar_terms_longitudes = solar_terms_longitudes

    def __call__(self, t):
        # 计算太阳的黄经
        astrometric = self.earth.at(t).observe(self.sun).apparent()
        ecliptic = astrometric.ecliptic_latlon()
        longitude = ecliptic[1].degrees % 360  # 使用黄经

        # 调整索引计算公式：从立春（315°）开始，每15°一个节气
        index = (np.floor((longitude - 315) / 15)).astype(int) % 24  # 计算节气索引
        return index

def get_solar_terms_dates(year):
    """
    使用 skyfield 库动态计算指定年份的24节气日期。
    返回一个字典，键为日期对象（基于UTC时间），值为节气名称。
    """
    ts = load.timescale()
    eph = load('de421.bsp')  # 天体历表

    # 创建自定义事件函数实例
    solar_terms_function = SolarTermsFunction(eph, SOLAR_TERMS_LONGITUDES)

    # 定义时间范围
    t0 = ts.utc(year, 1, 1)
    t1 = ts.utc(year + 1, 1, 1)

    # 使用 find_discrete 查找节气日期
    t, y = almanac.find_discrete(t0, t1, solar_terms_function)

    solar_terms_dates = {}
    for ti, yi in zip(t, y):
        # 获取UTC日期
        utc_datetime = ti.utc_datetime()
        date = utc_datetime.date()
        term = SOLAR_TERMS[yi % 24]
        solar_terms_dates[date] = term

    return solar_terms_dates

def get_zodiac(year):
    """
    根据年份计算生肖。
    """
    zodiacs = ["鼠", "牛", "虎", "兔", "龙", "蛇",
               "马", "羊", "猴", "鸡", "狗", "猪"]
    base_year = 1900  # 1900年是鼠年
    index = (year - base_year) % 12
    return zodiacs[index]

# 读取配置文件中的生日信息
config = configparser.ConfigParser()
config_path = 'config.ini' if os.path.isfile('config.ini') else 'config.sample.ini'
config.read(config_path, encoding='utf-8')

birthday_dict = {}
if 'birthdays' in config:
    for key, value in config.items('birthdays'):
        try:
            key_tuple = ast.literal_eval(key)
            value_list = [name.strip() for name in value.split(',')]
            # **优化点：将每两个人的姓名组合成一行**
            grouped_names = []
            for i in range(0, len(value_list), 2):
                group = ', '.join(value_list[i:i+2])
                grouped_names.append(group)
            birthday_dict[key_tuple] = grouped_names
        except Exception as e:
            print(f"配置文件中生日信息解析错误: {e}")

calendar.setfirstweekday(calendar.SUNDAY)


# 初始化Tkinter根窗口
root = tk.Tk()
root.title("万年历生成器 v0.35")
root.withdraw()

def get_birthday(solar_month, solar_day):
    birthdays = birthday_dict.get((solar_month, solar_day), [])
    formatted_birthdays = "\n".join(birthdays)
    return formatted_birthdays

def solar_to_lunar(solar_month, solar_day, year):
    try:
        solar_date = Solar(year, solar_month, solar_day)
        lunar_date = Converter.Solar2Lunar(solar_date)
        return (lunar_date.month, lunar_date.day)
    except Exception as e:
        return f"错误：{e}"

def get_lunar_date(solar_date, solar_terms_dates):
    try:
        lunar_date = Converter.Solar2Lunar(solar_date)
        # 使用正确的属性名
        lunar_month = lunar_date.month
        lunar_day = lunar_date.day
        lunar_day_chinese = lunar_day_to_chinese(lunar_day)

        # 使用UTC日期获取节气信息
        solar_term = solar_terms_dates.get(solar_date.to_date(), "")
        return f"{lunar_day_chinese}\n{solar_term}" if solar_term else f"{lunar_day_chinese}"
    except Exception as e:
        return f"错误：{e}"

def lunar_day_to_chinese(day):
    tens, ones = divmod(day, 10)
    chinese_tens = ["初", "十", "廿", "卅"]
    chinese_ones = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if day == 10:
        return "初十"
    elif day == 20:
        return "二十"
    elif day == 30:
        return "三十"
    else:
        return chinese_tens[tens] + (chinese_ones[ones-1] if ones > 0 else "")

def generate_calendar(year):
    solar_terms_dates = get_solar_terms_dates(year)
    zodiac = get_zodiac(year)  # 获取生肖
    file_path = filedialog.asksaveasfilename(
        defaultextension='.xlsx',
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="保存为"
    )

    if file_path:
        # 使用 openpyxl 直接操作 Excel
        wb = Workbook()
        ws = wb.active
        ws.title = f"{year} Calendar"

        # 设置页面布局为A4纵向
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 1  # 设置为1页高，确保整页内容

        # 设置页边距（英寸单位）
        # 1厘米 ≈ 0.393701英寸, 1.5厘米 ≈ 0.590551英寸
        margins = PageMargins(left=0.3, right=0.3, top=0.5, bottom=0.5)
        ws.page_margins = margins

        # 定义边框样式
        thin = Side(border_style="thin", color="000000")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # 定义填充颜色（可选）
        solar_term_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # 黄色

        # 定义字体
        title_font = Font(bold=True, size=20)          # 标题字体，20号，加粗
        merge_font = Font(bold=True, size=14)          # 增大月份标题字体大小为14号，保持加粗
        day_font_large = Font(bold=True, size=8.6)     # 字体大小为8.6， 加粗
        day_font = Font(bold=True, size=7.1)           # 默认字体大小为7.5， 加粗
        day_font_medium = Font(bold=True, size=11)     # 新增：字体大小为11， 加粗
        day_font_small = Font(bold=True, size=4)       # 字体大小为4，用于内容行数 >=5， 加粗
        align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)

        # 插入标题行
        title = f"{year}年{zodiac}年"
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=23)  # 跨越1-23列
        title_cell = ws.cell(row=1, column=1)
        title_cell.value = title
        title_cell.font = title_font
        title_cell.alignment = Alignment(horizontal='center', vertical='center')

        # 每行显示3个月，共4行
        months_per_row = 3
        row = 2  # 因为标题占据了第一行
        days_of_week_cn = ["日", "一", "二", "三", "四", "五", "六"]

        for quarter in range(0, 12, months_per_row):
            # 合并月份标题
            for month_offset in range(months_per_row):
                month = quarter + month_offset + 1
                col = month_offset * 8 + 1  # 每个月占7列，1列间隔
                month_name = f"{year}年{month}月"
                cell = ws.cell(row=row, column=col)
                cell.value = month_name
                cell.font = merge_font
                cell.alignment = align_center
                # 不应用边框到月份标题
                # 合并单元格
                ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+6)
            row +=1

            # 写入星期标题
            for month_offset in range(months_per_row):
                col = month_offset * 8 + 1
                for i, day in enumerate(days_of_week_cn):
                    cell = ws.cell(row=row, column=col + i)
                    cell.value = day
                    cell.font = merge_font
                    cell.alignment = align_center
                    cell.border = border  # 应用边框到星期标题
            row +=1

            # 获取每个月的日历
            month_calendars = []
            max_weeks = 6  # 固定每个月使用6周，以确保布局一致

            for month_offset in range(months_per_row):
                month = quarter + month_offset + 1
                cal = calendar.monthcalendar(year, month)
                # 确保每个月有6周
                while len(cal) < max_weeks:
                    cal.append([0]*7)
                month_calendars.append(cal)

            for week in range(max_weeks):
                for month_offset in range(months_per_row):
                    month = quarter + month_offset + 1
                    cal = month_calendars[month_offset]
                    col = month_offset * 8 + 1
                    week_days = cal[week]
                    for i, day in enumerate(week_days):
                        cell_col = col + i
                        if day != 0:
                            solar_date = Solar(year, month, day)
                            # 获取农历日期和节气信息
                            lunar_info = get_lunar_date(solar_date, solar_terms_dates)
                            # 获取生日信息
                            birthday = get_birthday(month, day)
                            # 组装单元格内容
                            cell_value = f"{day}\n{lunar_info}"
                            if birthday:
                                cell_value += f"\n{birthday}"
                            # 去除前后多余的换行符
                            cell_value = cell_value.strip('\n')
                            # 分割内容为行
                            lines = cell_value.split('\n')
                            # 估算自动换行导致的额外行数
                            # 设定每种字体对应的最大字符数
                            max_chars_per_font = {
                                'large': 5,    # day_font_large
                                'default': 8,  # day_font
                                'small': 10     # day_font_small
                            }
                            total_lines = 0
                            for line in lines:
                                # 计算每行需要多少实际显示行
                                if len(line) > max_chars_per_font['large']:
                                    # 向上取整
                                    wrapped_lines = math.ceil(len(line) / max_chars_per_font['large'])
                                    total_lines += wrapped_lines
                                else:
                                    total_lines +=1
                            # 选择字体大小
                            if total_lines == 2:
                                current_font = day_font_medium
                            elif total_lines <=3:
                                current_font = day_font_large
                            elif total_lines >=5:
                                current_font = day_font_small
                            else:
                                current_font = day_font
                            # 应用字体和设置单元格值
                            cell = ws.cell(row=row + week, column=cell_col)
                            cell.value = cell_value
                            cell.font = current_font
                            cell.alignment = align_center
                            cell.border = border  # 应用边框到日期单元格

                            # 如果有节气，应用填充颜色
                            date = datetime(year, month, day).date()
                            solar_term = solar_terms_dates.get(date, "")
                            if solar_term:
                                cell.fill = solar_term_fill
                        else:
                            cell = ws.cell(row=row + week, column=col + i)
                            cell.value = ""
                            cell.border = border  # 应用边框到空白单元格
            row += max_weeks  # 跳过已写入的周数

        # 设置列宽和行高以适应A4页面
        # 定义像素到openpyxl列宽的转换函数
        pixel_to_column_width = lambda px: (px - 5) / 7

        # 定义主列和分割列的像素宽度
        main_column_width_px = 62
        separator_column_width_px = 8

        # 转换为openpyxl列宽单位
        main_column_width = pixel_to_column_width(main_column_width_px)
        separator_column_width = pixel_to_column_width(separator_column_width_px)

        for col in range(1, 25):
            column_letter = get_column_letter(col)
            if col in [8, 16, 24]:  # 分割列
                ws.column_dimensions[column_letter].width = separator_column_width
            else:  # 主列
                ws.column_dimensions[column_letter].width = main_column_width

        # 行高设为56像素，转换为openpyxl单位（磅）
        pixel_to_points = lambda px: px * 72 / 96
        desired_row_height_px = 56  # 增加4像素
        row_height = pixel_to_points(desired_row_height_px)  # ≈42磅

        for row_num in range(1, ws.max_row + 1):
            ws.row_dimensions[row_num].height = row_height  # 设置为≈42磅

        # 设置打印选项以居中
        ws.print_options.horizontalCentered = True
        ws.print_options.verticalCentered = True

        # 删除默认创建的Sheet（如果存在）
        if 'Sheet' in wb.sheetnames:
            del wb['Sheet']

        wb.save(file_path)
        messagebox.showinfo("完成", f"{year}年的日历已生成并保存。")
    else:
        print("文件保存已取消。")

# 运行脚本
year = simpledialog.askinteger("输入年份", "请输入要打印的日历年份:", minvalue=2020, maxvalue=2030)

if year is not None:
    generate_calendar(year)
else:
    print("未输入年份。")
