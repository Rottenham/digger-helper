from extra import game_on, game_mode, game_ui, read_memory
from time import sleep
from os import system, path, get_terminal_size
from sys import stdout, executable
from re import search
from colorama import init
from cursor import hide

__title__ = "矿工法辅助"
__version__ = "1.4"
__author__ = "Crescendo"
__date__ = "22/05/27"
output_text = ""
magnet = None
x_offset = [[49, 543], [15, 577], [12, 580],
            [17, 575], [58, 534]]  # 5列磁对应的各行矿工x范围
out_placeholder = "ＯＵＴ"
est_delay = 35
offset_cache = 9999     # 记录上一次读取磁铁的偏移值，尽可能降低读内存数


def get_header():
    return f"{__title__} v{__version__} by {__author__} {__date__}\n当前延迟：{est_delay}cs（可在文件名中修改）"


def print_header():
    stdout.write(get_header() + "\n\n")
    stdout.flush()


def move_cursor_pos(y, x):
    print("\033[%d;%dH" % (y, x), end="")


def output(str, clear):
    global output_text
    if (output_text == str):
        return
    output_text = str
    if clear:
        system("cls")
        print_header()
    else:
        move_cursor_pos(4, 1)
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


def check_plant(i, plants_offset):
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


def get_magnet():
    global offset_cache
    plants_count_max = read_memory("unsigned int", 0x6A9EC0, 0x768, 0xB0)
    plants_offset = read_memory("unsigned int", 0x6A9EC0, 0x768, 0xAC)
    if offset_cache < plants_count_max:
        result = check_plant(offset_cache, plants_offset)
        if result is not None:
            return result
    for i in range(plants_count_max):
        result = check_plant(i, plants_offset)
        if result is not None:
            offset_cache = i
            return result
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
    digger_positions = []
    for start_x in (410, 650):
        digger_positions.append(calculate_digger_x(start_x, cd))
    for i in range(5):
        if abs(i - row) > 2:
            values += [out_placeholder, out_placeholder]
        else:
            m_lo, m_hi = get_limits(row, col, i)
            for digger_x in digger_positions:
                if digger_x < 10 or digger_x < m_lo or int(digger_x) > m_hi:
                    values.append(out_placeholder)
                else:
                    if digger_x < 100:
                        values.append(" {:.1f} ".format(digger_x))
                    else:
                        values.append("{:.1f} ".format(digger_x))
    return values


def get_digger_info():
    global magnet
    magnet = get_magnet()
    if magnet is None:  # 磁铁连续吸附时有1cs状态为1，尝试跳过
        sleep(0.02)
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
    init()
    print_header()
    while True:
        hide()
        if get_terminal_size()[0] < 35:
            output("命令行界面过窄，请调整窗口大小", clear=True)
            sleep(0.01)
        elif not game_on():
            output("未找到游戏（支持的版本：英原、汉一、汉二）", clear=True)
            sleep(0.3)
        elif game_mode() != 70 or not game_ui() in [2, 3]:
            output("已找到游戏，但未进入IZE", clear=True)
            sleep(0.3)
        else:
            output(get_digger_info(), clear=False)
            if magnet is None:
                sleep(0.3)
            else:
                sleep(0.01)


if __name__ == "__main__":
    main()

# pyinstaller --onefile digger_helper.py
