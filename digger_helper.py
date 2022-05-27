from extra import game_on, game_mode, game_ui, read_memory
from os import system, path
from sys import stdout, executable
from re import search

__title__ = "矿工法助手"
__version__ = "1.1"
__author__ = "Crescendo"
__date__ = "22/05/27"
output_text = ""
magnet = None
x_offset = [[49, 543], [15, 577], [12, 580],
            [17, 575], [58, 534]]  # 5列磁对应的各行矿工x范围
out_placeholder = "ＯＵＴ"
est_delay = 35


def get_header():
    return __title__ + " v" + __version__ + " by " + __author__ + " " + __date__ + "\n当前延迟：" + str(est_delay) + "cs（可在文件名中修改）"


def output(str):
    global output_text
    if (output_text == str):
        return
    output_text = str
    system("cls")
    stdout.write(get_header() + "\n\n")
    stdout.write(str)
    stdout.flush()


def format_with_box(values):
    str = """================================
|　行数　|　６列矿　|　９列矿　|
|　１　　|　{}　|　{}　|
|　２　　|　{}　|　{}　|
|　３　　|　{}　|　{}　|
|　４　　|　{}　|　{}　|
|　５　　|　{}　|　{}　|
================================"""
    return str.format(*values)


def no_magenet():
    str = """================================
|　　　　 　　　　　 　　　　　|
|　　　　 　　　　　 　　　　　|
|　　　　　尚未引磁　　　　　　|
|　　　　 　　　　　 　　　　　|
|　　　　 　　　　　 　　　　　|
|　　　　 　　　　　 　　　　　|
================================"""
    return str


def get_magnet():
    plants_count_max = read_memory("unsigned int", 0x6A9EC0, 0x768, 0xB0)
    plants_offset = read_memory("unsigned int", 0x6A9EC0, 0x768, 0xAC)
    for i in range(plants_count_max):
        plant_dead = read_memory("bool", plants_offset + 0x141 + 0x14C * i)
        plant_crushed = read_memory("bool", plants_offset + 0x142 + 0x14C * i)
        plant_type = read_memory("int", plants_offset + 0x24 + 0x14C * i)
        plant_state = read_memory("int", plants_offset + 0x3C + 0x14C * i)
        if not plant_dead and not plant_crushed and plant_type == 31 and (plant_state == 26 or plant_state == 27):
            magnet_row = read_memory("int", plants_offset + 0x1C + 0x14C * i)
            magnet_col = read_memory("int", plants_offset + 0x28 + 0x14C * i)
            magnet_cd = read_memory("int", plants_offset + 0x54 + 0x14C * i)
            return (magnet_row, magnet_col, magnet_cd)
    return None


def get_limits(magnet_row, magnet_col, digger_row):
    lo = x_offset[digger_row - magnet_row + 2][0] + (magnet_col - 4) * 80
    hi = x_offset[digger_row - magnet_row + 2][1] + (magnet_col - 4) * 80
    return (lo, hi)


def calculate_digger_x(start_x, cd):
    if cd <= 0:
        return start_x
    if cd <= 500:
        x = start_x - 0.68 * cd
    else:
        x = start_x - 0.68 * 500 - 0.67 * (cd - 500)
    if x < 10:
        x = 9
    return x


def get_values(magnet):
    global est_delay
    values = []
    row, col, cd = magnet
    cd -= est_delay
    for i in range(5):
        if abs(i - row) > 2:
            values += [out_placeholder, out_placeholder]
        else:
            m_lo, m_hi = get_limits(row, col, i)
            for start_x in (410, 650):
                digger_x = calculate_digger_x(start_x, cd)
                if digger_x < 10 or digger_x < m_lo or int(digger_x) > m_hi:
                    values.append(out_placeholder)
                else:
                    if digger_x < 100:
                        values.append("{:.1f}　".format(digger_x))
                    else:
                        values.append("{:.1f} ".format(digger_x))
    return values


def get_digger_info():
    global magnet
    magnet = get_magnet()
    if magnet is None:
        return no_magenet()
    else:
        values = get_values(magnet)
        return format_with_box(values)


def get_delay():
    global est_delay
    exe_name = path.basename(executable)
    delay_text = exe_name[exe_name.rfind(
        "d=")+2:exe_name.rfind(".")]
    match = search(r'(\d+)', delay_text)
    if match:
        delay_text = match.group(1)
        if delay_text.isdigit():
            delay_num = int(delay_text)
            if delay_num >= 0 and delay_num <= 100:
                est_delay = delay_num

def main():
    get_delay()
    while True:
        if not game_on():
            output("未找到游戏（支持的版本：英原、汉一、汉二）")
        else:
            if game_mode() != 70 or (game_ui() != 2 and game_ui() != 3):
                output(f"已找到游戏，但未进入IZE")
            else:
                output(get_digger_info())


if __name__ == "__main__":
    main()

# pyinstaller --onefile digger_helper.py
