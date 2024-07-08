import curses
import os
import json

def load_syntax_config():
    with open('icainit.json', 'r') as file:
        return json.load(file)

def apply_syntax_highlighting(line, syntax_config):
    highlighted_line = []
    idx = 0
    while idx < len(line):
        match = False
        
        # Check for keywords
        for keyword in syntax_config['keywords']:
            if line.startswith(keyword, idx):
                highlighted_line.append((keyword, curses.color_pair(2)))  # Color 2 for keywords
                idx += len(keyword)
                match = True
                break

        # Check for language functions
        if not match:
            for lang_func in syntax_config['languagefuncs']:
                if line.startswith(lang_func, idx):
                    highlighted_line.append((lang_func, curses.color_pair(4)))  # Color 4 for language functions
                    idx += len(lang_func)
                    match = True
                    break

        # Check for strings
        if not match:
            if line[idx] in syntax_config['strings']:
                string_char = line[idx]
                end_idx = idx + 1
                while end_idx < len(line) and line[end_idx] != string_char:
                    end_idx += 1
                if end_idx < len(line):
                    end_idx += 1
                highlighted_line.append((line[idx:end_idx], curses.color_pair(5)))  # Color 5 for strings
                idx = end_idx
                match = True

        # Check for comments
        if not match:
            for comment in syntax_config['comment']:
                if line.startswith(comment, idx):
                    highlighted_line.append((line[idx:], curses.color_pair(6)))  # Color 6 for comments
                    idx = len(line)
                    match = True
                    break

        # If no match, just add the character as is
        if not match:
            highlighted_line.append((line[idx], curses.color_pair(1)))  # Default color pair
            idx += 1

    return highlighted_line

def main(stdscr):
    curses.curs_set(1)  # Mostrar o cursor
    stdscr.keypad(True)  # Habilitar leitura de teclas especiais
    stdscr.scrollok(True)
    
    # Inicializar pares de cores
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Texto padrão
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Palavras-chave
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Funções da linguagem
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Strings
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Comentários

    # Carregar configuração de sintaxe
    syntax_config = load_syntax_config()

    # Inicializar variáveis
    file_content = [""]
    file_path = ""
    cursor_x = 0
    cursor_y = 0
    command_mode = False
    command_buffer = ""
    scroll_offset = 0
    horizontal_offset = 0

    def load_file(path):
        nonlocal file_content, cursor_x, cursor_y, scroll_offset, horizontal_offset
        try:
            with open(path, 'r') as file:
                file_content = file.readlines()
            file_content = [line.rstrip('\n') for line in file_content]
        except FileNotFoundError:
            file_content = [""]
        cursor_x = 0
        cursor_y = 0
        scroll_offset = 0
        horizontal_offset = 0

    def save_file(path):
        with open(path, 'w') as file:
            for line in file_content:
                file.write(line + '\n')

    def display_editor():
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        for idx, line in enumerate(file_content[scroll_offset:], start=scroll_offset):
            if idx - scroll_offset >= h - 2:
                break
            display_line = line[horizontal_offset:horizontal_offset + w - 5]
            highlighted_line = apply_syntax_highlighting(display_line, syntax_config)
            stdscr.addstr(idx - scroll_offset, 0, f"{idx+1:4} ")
            for text, color in highlighted_line:
                stdscr.addstr(text, color)

        if command_mode:
            stdscr.addstr(h-1, 0, f":{command_buffer}")
        stdscr.refresh()

    def handle_input():
        nonlocal cursor_x, cursor_y, command_mode, command_buffer, file_path, scroll_offset, horizontal_offset
        while True:
            if command_mode:
                stdscr.move(stdscr.getmaxyx()[0]-1, len(command_buffer)+1)
                key = stdscr.getch()
                if key == 10:  # Enter key
                    if command_buffer.startswith("save "):
                        save_file(command_buffer[5:].strip())
                    elif command_buffer.startswith("edit "):
                        load_file(command_buffer[5:].strip())
                    elif command_buffer == "exit":
                        break
                    command_buffer = ""
                    command_mode = False
                elif key == 27:  # ESC key
                    command_buffer = ""
                    command_mode = False
                elif key == curses.KEY_BACKSPACE or key == 127:
                    command_buffer = command_buffer[:-1]
                elif 32 <= key <= 126:  # Printable ASCII characters
                    command_buffer += chr(key)
            else:
                h, w = stdscr.getmaxyx()
                max_y = min(len(file_content), h - 2) - 1

                if cursor_y - scroll_offset < 0 or cursor_y - scroll_offset >= h - 2 or (cursor_x - horizontal_offset) + 5 >= w:
                    continue

                stdscr.move(cursor_y - scroll_offset, (cursor_x - horizontal_offset) + 5)
                key = stdscr.getch()
                
                if key == curses.KEY_UP:
                    if cursor_y > 0:
                        cursor_y -= 1
                        if cursor_y < scroll_offset:
                            scroll_offset -= 1
                elif key == curses.KEY_DOWN:
                    if cursor_y < len(file_content) - 1:
                        cursor_y += 1
                        if cursor_y - scroll_offset >= h - 2:
                            scroll_offset += 1
                elif key == curses.KEY_LEFT:
                    if cursor_x > 0:
                        cursor_x -= 1
                        if cursor_x < horizontal_offset:
                            horizontal_offset -= 1
                elif key == curses.KEY_RIGHT:
                    if cursor_x < len(file_content[cursor_y]):
                        cursor_x += 1
                        if cursor_x - horizontal_offset >= w - 5:
                            horizontal_offset += 1
                elif key == curses.KEY_BACKSPACE or key == 127:
                    if cursor_x > 0:
                        line = file_content[cursor_y]
                        file_content[cursor_y] = line[:cursor_x-1] + line[cursor_x:]
                        cursor_x -= 1
                        if cursor_x < horizontal_offset:
                            horizontal_offset = max(horizontal_offset - 1, 0)
                    elif cursor_y > 0:
                        cursor_x = len(file_content[cursor_y - 1])
                        file_content[cursor_y - 1] += file_content.pop(cursor_y)
                        cursor_y -= 1
                        if cursor_y < scroll_offset:
                            scroll_offset -= 1
                elif key == 10:  # Enter key
                    line = file_content[cursor_y]
                    file_content[cursor_y] = line[:cursor_x]
                    file_content.insert(cursor_y + 1, line[cursor_x:])
                    cursor_x = 0
                    cursor_y += 1
                    if cursor_y - scroll_offset >= h - 2:
                        scroll_offset += 1
                    horizontal_offset = 0
                elif key == 9:  # Tab key
                    line = file_content[cursor_y]
                    file_content[cursor_y] = line[:cursor_x] + " " * 4 + line[cursor_x:]
                    cursor_x += 4
                    if cursor_x - horizontal_offset >= w - 5:
                        horizontal_offset += 4
                elif 32 <= key <= 126:  # Printable ASCII characters
                    line = file_content[cursor_y]
                    file_content[cursor_y] = line[:cursor_x] + chr(key) + line[cursor_x:]
                    cursor_x += 1
                    if cursor_x - horizontal_offset >= w - 5:
                        horizontal_offset += 1
                elif key == 27:  # ESC key
                    command_mode = True

                if cursor_y >= len(file_content):
                    file_content.append("")
                
                cursor_y = min(cursor_y, len(file_content) - 1)

                # Verificar se a linha atual precisa ser rolada horizontalmente
                if cursor_x < horizontal_offset:
                    horizontal_offset = cursor_x
                elif cursor_x - horizontal_offset >= w - 5:
                    horizontal_offset = cursor_x - (w - 6)

            display_editor()

    load_file(file_path)
    display_editor()
    handle_input()

curses.wrapper(main)
