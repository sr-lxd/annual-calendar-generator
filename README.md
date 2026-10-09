# 年历生成器

这是一个 Windows 桌面程序，可按指定年份生成一张 Excel 年历。主程序为 `年历生成器v0.35.py`。它把 12 个月排成 3 列、4 行，显示公历日期、农历日期、二十四节气和可选生日，并按 A4 纵向页面设置。

仓库也保留了 `sofia万年历生成器v0.18.py` 作为辅助工具。它根据本地 Excel 名单生成生日配置，供年历主程序读取。主程序本身不读取身份证号码。

## 功能

- 选择 2020—2030 年，生成该年的完整年历。
- 计算公历日期、农历日期和二十四节气；节气日期由 Skyfield 根据 DE421 星历计算。
- 根据年份显示生肖。
- 可从 `config.ini` 读取生日标记，并与对应日期一起显示。
- 将 12 个月排入单张工作表，按 A4 纵向页面设置并输出为 `.xlsx`。
- 主程序启动时优先读取本机 `config.ini`；没有该文件时读取 `config.sample.ini` 中的虚构示例。

## 运行环境

- Windows 10 或 Windows 11
- Python 3.10 或更高版本
- Python 自带的 Tkinter 组件

## 安装和启动

在项目目录打开 PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python ".\年历生成器v0.35.py"
```

程序先弹出年份输入框，再弹出保存位置选择框。选择输出文件名后，等待计算完成；成功时会显示完成提示。默认允许选择 2020—2030 年。

项目包含 `de421.bsp` 星历文件。Skyfield 还可能在首次运行时下载时间尺度数据；其默认下载位置是启动程序时的当前目录。可从 [Skyfield 数据文件说明](https://rhodesmill.org/skyfield/files/) 查看细节。

## 生日配置

主程序读取 `config.ini` 的 `[birthdays]` 区段。每个键是 `(月, 日)`，值是逗号分隔的显示名称：

```ini
[birthdays]
(1, 1): 元旦, 示例人员甲
(6, 15): 示例人员乙
```

仓库中的 `config.sample.ini` 使用虚构姓名和日期。你可以复制它并在本机改名为 `config.ini`，也可以使用辅助工具生成自己的配置。若本机 `config.ini` 存在，主程序会优先使用它；该文件被 Git 忽略，不会进入提交。

### 使用辅助工具生成生日配置

`sofia万年历生成器v0.18.py` 会读取当前目录的 `身份证号.xlsx`，要求列名为“姓名”和“身份证号”，从身份证号码中提取出生月日，并写出 `config.ini`。生成文件会包含姓名与生日；已有配置会先被改名为 `config_1.ini`、`config_2.ini` 等。

1. 在本机 Excel 中准备 `身份证号.xlsx`，确保身份证号列按文本保存。
2. 在项目目录运行：

   ```powershell
   python ".\sofia万年历生成器v0.18.py"
   ```

3. 选择年份，点击“生成 config.ini”。
4. 再运行 `年历生成器v0.35.py`，生成带生日标记的年历。

也可以跳过辅助工具，直接用 `config.sample.ini` 演示年历中的生日显示。

## 隐私

- 身份证号码属于敏感个人信息。辅助工具在本机读取 `身份证号.xlsx`；请只处理获得授权的数据。
- 真实的 `身份证号.xlsx`、年历输出工作簿、`config.ini` 和 `config_*.ini` 均被 `.gitignore` 排除。不要用 `git add -f` 强行加入这些文件。
- 公开仓库只包含虚构的 `config.sample.ini` 和通用 `festivals.ini` 示例，不包含真实姓名、生日、身份证号码或组织内部活动。
- 辅助工具不会联网上传输入表或生日配置。

## 项目文件

| 文件 | 用途 |
| --- | --- |
| `年历生成器v0.35.py` | 年历主程序，生成 Excel 年历 |
| `de421.bsp` | 主程序计算二十四节气所需的星历数据 |
| `config.sample.ini` | 主程序可读取的虚构生日示例 |
| `sofia万年历生成器v0.18.py` | 辅助生日与节日配置生成器 |
| `festivals.ini` | 辅助工具使用的通用节日样例 |
| `requirements.txt` | Python 第三方依赖 |
| `.gitignore` | 排除身份证名单、私人配置和生成结果 |

## 许可

本项目尚未声明项目代码的开源许可证。公开可见不等于授予复制、修改或分发代码的许可。Skyfield、lunarcalendar、pandas、NumPy、openpyxl 和 lunardate 按各自上游项目的许可条款提供。
