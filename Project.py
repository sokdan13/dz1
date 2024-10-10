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
                current[path_parts[-1]] = {}
            else:
                current[path_parts[-1]] = member
        return file_tree

    def list_dir(self, path):
        node = self.get_node(path)
        if node is not None and isinstance(node, dict):
            dirs = [item + '/' for item in node if isinstance(node[item], dict)]
            files = [item for item in node if not isinstance(node[item], dict)]
            return dirs, files
        return [], []

    def change_dir(self, path):
        if path == "/":
            self.current_dir = "/bs"
        elif path == "..":
            if self.current_dir != "/bs":
                self.current_dir = "/".join(self.current_dir.strip('/').split('/')[:-1])
                if not self.current_dir:
                    self.current_dir = "/bs"
        else:
            new_dir = os.path.join(self.current_dir, path).replace("\\", "/").strip('/')
            if new_dir and self.get_node(new_dir):
                self.current_dir = '/' + new_dir
            else:
                raise FileNotFoundError

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

        self.output = scrolledtext.ScrolledText(root, height=20, width=80, state=tk.DISABLED, bg="blue", fg="white")
        self.output.pack()

        self.input = tk.Entry(root, width=80)
        self.input.pack()

        self.username = username
        self.vfs = vfs
        self.update_prompt()

    def update_prompt(self):
        prompt = f"{self.username}@virtual:{self.vfs.current_dir}$ "
        self.input.delete(0, tk.END)
        self.input.insert(0, prompt)
        self.input.icursor(len(prompt))






def main():
    parser = argparse.ArgumentParser(description="Shell Emulator")
    parser.add_argument('--user', required=True, help="Username for shell prompt")
    parser.add_argument('--vfs', required=True, help="Path to the virtual file system (tar archive)")
    parser.add_argument('--script', help="Path to the startup script")

    args = parser.parse_args()

    vfs = VirtualFileSystem(args.vfs)
    root = tk.Tk()
    shell = ShellEmulator(root, args.user, vfs)


    root.mainloop()


if __name__ == "__main__":
    main()
