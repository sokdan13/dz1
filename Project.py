import os
import tarfile
import argparse
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime


class VirtualFileSystem:
    def __init__(self, tar_path):
        self.tar_path = tar_path
        self.tar = tarfile.open(tar_path, 'r')
        self.current_dir = '/bs'
        self.file_tree = self.build_file_tree()

    def build_file_tree(self):
        file_tree = {}
        for member in self.tar.getmembers():
            path_parts = member.name.strip('/').split('/')
            current = file_tree
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            if member.isdir():
                current[path_parts[-1]] = {}  # Папка, даже если она пустая
            else:
                current[path_parts[-1]] = member  # Файл
        return file_tree

    def list_dir(self, path):
        node = self.get_node(path)
        if node is not None and isinstance(node, dict):
            dirs = [item + '/' for item in node if isinstance(node[item], dict)]
            files = [item for item in node if not isinstance(node[item], dict)]
            return dirs, files
        return [], []

    def change_dir(self, path):
        # Если путь абсолютный
        if path == "/":
            self.current_dir = "/bs"
            return

        # Разбиваем путь на сегменты
        parts = path.split('/')

        # Строим новый путь относительно текущего каталога
        if path.startswith('/'):
            new_dir = ["bs"]  # Абсолютный путь от корня
        else:
            new_dir = self.current_dir.strip('/').split('/')  # Относительный путь от текущего каталога

        for part in parts:
            if part == "..":
                # Переход на уровень выше
                if len(new_dir) > 1:  # Чтобы не выйти за корневую директорию
                    new_dir.pop()
            elif part == "." or part == "":  # Игнорируем текущий каталог (".") и пустые сегменты
                continue
            else:
                new_dir.append(part)

        # Собираем полный путь
        full_path = "/" + "/".join(new_dir).strip('/')

        # Проверяем, что конечный путь существует в виртуальной файловой системе
        if self.get_node(full_path) is not None:
            self.current_dir = full_path
        else:
            raise FileNotFoundError(f"cd: no such file or directory: {path}")

    def get_node(self, path):
        """ Возвращает узел (файл или директорию) по заданному пути. """
        parts = path.strip("/").split('/')
        current = self.file_tree
        for part in parts:
            if part and part in current:
                current = current[part]
            else:
                return None  # Если узел не найден, возвращаем None
        return current  # Возвращает файл или директорию, включая пустые папки

    def get_node(self, path):
        """ Возвращает узел (файл или директорию) по заданному пути. """
        parts = path.strip("/").split('/')
        current = self.file_tree
        for part in parts:
            if part and part in current:
                current = current[part]
            else:
                return None  # Если узел не найден, возвращаем None
        return current  # Возвращает файл или директорию, включая пустые папки

    def remove(self, path):
        full_path = os.path.join(self.current_dir, path).replace("\\", "/").strip('/')
        parts = full_path.split('/')
        node = self.file_tree
        for part in parts[:-1]:
            node = node[part]
        del node[parts[-1]]

    def get_node(self, path):
        parts = path.strip("/").split('/')
        current = self.file_tree
        for part in parts:
            if part and part in current:
                current = current[part]
            else:
                return None
        return current






class ShellEmulator:
    def __init__(self, root, username, vfs):
        self.root = root
        self.root.title("Shell Emulator")
        self.prompt_length = 0  # Новый атрибут для хранения длины приглашения

        self.output = scrolledtext.ScrolledText(root, height=20, width=80, state=tk.DISABLED, bg="black", fg="white")
        self.output.pack()

        self.input = tk.Entry(root, width=80)
        self.input.pack()
        self.input.bind("<Return>", self.run_command)
        self.input.bind("<KeyPress>", self.on_key_press)  # Обработка нажатий клавиш

        self.username = username
        self.vfs = vfs
        self.update_prompt()

    def on_key_press(self, event):
        # Блокируем удаление текста до позиции приглашения
        if self.input.index(tk.INSERT) < self.prompt_length and event.keysym in ("BackSpace", "Left"):
            return "break"  # Останавливаем стандартное поведение

    def update_prompt(self):
        if self.vfs.current_dir == "/bs":
            prompt_dir = "~"
        else:
            prompt_dir = self.vfs.current_dir.replace("/bs", "~", 1)  # Заменяем /bs на ~ для подкаталогов

        prompt = f"{self.username}@virtual:{prompt_dir}$ "
        self.input.delete(0, tk.END)
        self.input.insert(0, prompt)
        self.input.icursor(len(prompt))
        self.prompt_length = len(prompt)  # Сохраняем длину приглашения

    def run_command(self, event):
        command_input = self.input.get().split('$', 1)[-1].strip()

        if self.vfs.current_dir == "/bs":
            display_dir = "~"
        else:
            display_dir = self.vfs.current_dir.replace("/bs", "~", 1)

        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END,
                           f"{self.username}@virtual:{display_dir}$ {command_input}\n")  # Добавлен перевод строки
        self.execute_command(command_input)
        self.update_prompt()
        self.output.config(state=tk.DISABLED)

    def execute_command(self, command):
        parts = command.split()
        if not parts:
            return
        cmd = parts[0]

        if cmd == "ls":
            flags = [p for p in parts if p.startswith('-')]
            self.ls(flags)
        elif cmd == "cd":
            if len(parts) > 1:
                self.cd(parts[1])
            else:
                self.write_output("cd: missing operand\n")
        elif cmd == "rm":
            if len(parts) > 1:
                self.rm(parts[1])
            else:
                self.write_output("rm: missing operand\n")
        elif cmd == "echo":
            self.echo(" ".join(parts[1:]))
        elif cmd == "exit":
            self.root.quit()
        else:
            self.write_output(f"{cmd}: command not found\n")

            self.echo(" ".join(parts[1:]))

    def ls(self, flags=[]):
        try:
            dirs, files = self.vfs.list_dir(self.vfs.current_dir)
            output = []

            if '-l' in flags:
                for d in dirs:
                    output.append(self.format_entry(d, is_dir=True, flags=flags))
                for f in files:
                    output.append(self.format_entry(f, is_dir=False, flags=flags))
            else:
                output = dirs + files

            if not output:
                self.write_output("\n")
            else:
                self.write_output("\n".join(output) + "\n")
        except FileNotFoundError:
            self.write_output(f"ls: cannot access '{self.vfs.current_dir}': No such directory\n")

    def format_entry(self, entry, is_dir, flags):
        node = self.vfs.get_node(os.path.join(self.vfs.current_dir, entry.strip('/')))
        info = node if not isinstance(node, dict) else None
        size = info.size if info else 0

        size_str = self.human_readable_size(size) if '-h' in flags else str(size)
        file_type = 'd' if is_dir else '-'
        permissions = 'rw-r--r--'
        links = 1
        owner = 'root'
        group = 'root'
        mtime = datetime.fromtimestamp(info.mtime).strftime('%b %d %Y') if info else ''
        return f"{file_type}{permissions} {links} {owner} {group} {size_str:>8} {mtime} {entry}"

    def human_readable_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"

    def cd(self, path):
        try:
            self.vfs.change_dir(path)
        except FileNotFoundError:
            self.write_output(f"cd: no such file or directory: {path}\n")

    def rm(self, path):
        try:
            self.vfs.remove(path)
            self.write_output(f"Removed {path}\n")
        except FileNotFoundError:
            self.write_output(f"rm: cannot remove '{path}': No such file or directory\n")

    def echo(self, text):
        self.write_output(text + "\n")

    def write_output(self, text):
        self.output.config(state=tk.NORMAL)  # Включаем возможность редактирования
        self.output.insert(tk.END, text)  # Вставляем текст в конец
        self.output.see(tk.END)  # Прокручиваем до конца
        self.output.config(state=tk.DISABLED)  # Блокируем редактирование





def main():
    parser = argparse.ArgumentParser(description="Shell Emulator")
    parser.add_argument('--user', required=True, help="Username for shell prompt")
    parser.add_argument('--vfs', required=True, help="Path to the virtual file system (tar archive)")
    parser.add_argument('--script', help="Path to the startup script")

    args = parser.parse_args()

    vfs = VirtualFileSystem(args.vfs)
    root = tk.Tk()
    shell = ShellEmulator(root, args.user, vfs)

    if args.script:
        execute_script(args.script, shell)

    root.mainloop()


def execute_script(script_path, shell):
    try:
        with open(script_path, 'r') as file:
            commands = file.readlines()
        for command in commands:
            command = command.strip()
            if command:
                shell.input.delete(0, tk.END)
                shell.input.insert(0, command)
                shell.run_command(None)
        shell.write_output(f"Startup script {script_path} executed successfully.\n")
    except FileNotFoundError:
        shell.write_output(f"Script file not found: {script_path}\n")
    except Exception as e:
        shell.write_output(f"Error executing script: {e}\n")

if __name__ == "__main__":
    main()