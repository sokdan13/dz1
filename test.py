import unittest
from io import StringIO
import sys
import os
import tarfile
from Project import VirtualFileSystem, ShellEmulator  # Подключаем основной проект


class TestShellEmulator(unittest.TestCase):

    def setUp(self):
        # Указываем путь к виртуальной файловой системе
        tar_path = r'C:\Users\Lenovo\PycharmProjects\dz1\gs.tar'

        # Настраиваем виртуальную файловую систему и оболочку
        self.vfs = VirtualFileSystem(tar_path)
        self.root = None  # Мы не запускаем графический интерфейс, поэтому root не нужен
        self.username = "user"
        self.shell = ShellEmulator(self.root, self.username, self.vfs)

        # Перенаправляем вывод на строковый буфер для проверки результатов
        self.old_stdout = sys.stdout
        sys.stdout = self.output = StringIO()

    def tearDown(self):
        # Восстанавливаем стандартный вывод
        sys.stdout = self.old_stdout

    def test_ls(self):
        # Тест команды ls
        self.shell.execute_command("ls")
        output = self.output.getvalue().strip()
        self.assertIn("cool/", output)
        self.assertIn("media/", output)

        # Тест команды ls -l
        self.output.truncate(0)
        self.output.seek(0)
        self.shell.execute_command("ls -l")
        output = self.output.getvalue().strip()
        self.assertIn("drw-r--r--", output)  # Права доступа для директорий
        self.assertIn("root", output)  # Владелец
        self.assertIn("media", output)  # Имя директории

        # Тест команды ls -lh
        self.output.truncate(0)
        self.output.seek(0)
        self.shell.execute_command("ls -lh")
        output = self.output.getvalue().strip()
        self.assertIn("KB", output)  # Проверяем, что размер в человеко-читаемом формате

    def test_cd(self):
        # Тест команды cd
        self.shell.execute_command("cd media")
        self.assertEqual(self.vfs.current_dir, "/bs/media")

        # Тест команды cd ..
        self.shell.execute_command("cd ..")
        self.assertEqual(self.vfs.current_dir, "/bs")

        # Тест команды cd / (в корневой каталог)
        self.shell.execute_command("cd /")
        self.assertEqual(self.vfs.current_dir, "/bs")

        # Тест команды cd ../../ (возврат на несколько уровней вверх)
        self.shell.execute_command("cd ../../")
        self.assertEqual(self.vfs.current_dir, "/bs")  # Уже в корне, не изменится

    def test_echo(self):
        # Тест команды echo
        self.shell.execute_command("echo Hello World")
        output = self.output.getvalue().strip()
        self.assertIn("Hello World", output)

    def test_rm(self):
        # Тест команды rm
        self.shell.execute_command("rm cool")
        dirs, files = self.vfs.list_dir("/bs")
        self.assertNotIn("cool/", dirs)

    def test_prompt(self):
        # Тест, что корневая директория отображается как ~
        self.shell.execute_command("cd /")
        self.assertEqual(self.shell.input.get(), f"{self.username}@virtual:~$ ")

        # Тест, что подкаталог отображается корректно
        self.shell.execute_command("cd media")
        self.assertEqual(self.shell.input.get(), f"{self.username}@virtual:~/media$ ")


def create_test_tar(tar_path, source_dir):
    # Функция для создания тестовой файловой системы в формате tar
    if not os.path.exists(source_dir):
        os.makedirs(source_dir)
        os.makedirs(os.path.join(source_dir, 'cool'))
        os.makedirs(os.path.join(source_dir, 'media'))

    with tarfile.open(tar_path, "w") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


if __name__ == "__main__":
    unittest.main()
