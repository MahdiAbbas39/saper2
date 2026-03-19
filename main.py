import sys, os, subprocess, threading
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal


# عنصر مخصص لعرض (الاسم + المسار) في القوائم
class FileItemWidget(QWidget):
    def __init__(self, path):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        name = os.path.basename(path)
        self.lbl_name = QLabel(name)
        self.lbl_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #3b8ed0;")

        self.lbl_path = QLabel(path)
        self.lbl_path.setStyleSheet("font-size: 12px; color: #888;")

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.lbl_path)


class SaberApp(QWidget):
    search_done = Signal(list)
    search_cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Saber | سابر")
        self.setFixedSize(1000, 750)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.history_file = "saber_history.txt"
        self.stop_flag = False

        self.setStyleSheet("""
            QWidget { background-color: #0f111a; color: white; font-family: 'Segoe UI'; }
            QLineEdit { background-color: #1a1c2e; border: 2px solid #3b8ed0; border-radius: 8px; padding: 10px; font-size: 15px; }
            QListWidget { background-color: #161925; border: 1px solid #2d3142; border-radius: 8px; outline: none; }
            QListWidget::item:selected { background-color: #2a2e45; border-radius: 5px; }
            QLabel#section_title { font-size: 18px; font-weight: bold; color: #bbb; margin-top: 10px; }
            QPushButton#clear_btn { background-color: #e74c3c; color: white; border-radius: 5px; font-weight: bold; padding: 5px; }
            QPushButton#clear_btn:hover { background-color: #c0392b; }
        """)

        self.init_ui()
        self.load_history()

        self.search_done.connect(self.on_search_done)
        self.search_cancelled.connect(self.reset_btn)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # العنوان
        title = QLabel("Saber | سابر")
        title.setStyleSheet("font-size: 35px; font-weight: bold; color: #3b8ed0;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # شريط البحث
        search_bar = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("أدخل اسم الملف بدقة...")

        self.btn = QPushButton("بحث")
        self.btn.setFixedSize(100, 45)
        self.reset_btn()
        self.btn.clicked.connect(self.toggle_search)

        search_bar.addWidget(self.btn)
        search_bar.addWidget(self.input)
        layout.addLayout(search_bar)

        # قائمة النتائج
        res_lbl = QLabel("النتائج:")
        res_lbl.setObjectName("section_title")
        layout.addWidget(res_lbl)

        self.res_list = QListWidget()
        self.res_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.res_list)

        # --- قسم الهستوري مع زر المسح ---
        hist_header = QHBoxLayout()
        hist_lbl = QLabel("سجل الملفات المفتوحة (الهستوري):")
        hist_lbl.setObjectName("section_title")

        self.clear_btn = QPushButton("مسح السجل")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setFixedSize(100, 30)
        self.clear_btn.clicked.connect(self.clear_history)

        hist_header.addWidget(hist_lbl)
        hist_header.addStretch()  # عشان يدفع الزر لليسار
        hist_header.addWidget(self.clear_btn)

        layout.addLayout(hist_header)

        self.hist_list = QListWidget()
        self.hist_list.setFixedHeight(150)
        self.hist_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.hist_list)

    def toggle_search(self):
        if self.btn.text() == "بحث":
            self.start_search()
        else:
            self.stop_flag = True

    def start_search(self):
        target = self.input.text().strip().lower()
        if not target: return

        self.stop_flag = False
        self.res_list.clear()
        self.btn.setText("إلغاء البحث")
        self.btn.setStyleSheet(
            "background-color: #e74c3c; color: white; border-radius: 8px; font-weight: bold; font-size: 14px;")

        threading.Thread(target=self.run_search, args=(target,), daemon=True).start()

    def run_search(self, target):
        results = []
        ignore_dirs = {"windows", "program files", "program files (x86)", "appdata"}

        for root, dirs, files in os.walk("C:\\"):
            if self.stop_flag:
                self.search_cancelled.emit()
                return
            dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs]
            for item in dirs + files:
                if self.stop_flag:
                    self.search_cancelled.emit()
                    return
                name, _ = os.path.splitext(item.lower())
                if item.lower() == target or name == target:
                    results.append(os.path.join(root, item))

        self.search_done.emit(results)

    def on_search_done(self, results):
        self.reset_btn()
        for path in results:
            self.add_item_to_list(self.res_list, path)
        if not results:
            self.input.setPlaceholderText("لم يتم العثور على شيء...")

    def reset_btn(self):
        self.btn.setText("بحث")
        self.btn.setStyleSheet(
            "background-color: #3b8ed0; color: white; border-radius: 8px; font-weight: bold; font-size: 14px;")

    def add_item_to_list(self, list_widget, path):
        item = QListWidgetItem(list_widget)
        widget = FileItemWidget(path)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, path)
        list_widget.addItem(item)
        list_widget.setItemWidget(item, widget)

    def open_file(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        subprocess.Popen(rf'explorer /select,"{path}"')
        self.save_to_history(path)

    def save_to_history(self, path):
        history_paths = self.get_history_paths()
        if path in history_paths:
            history_paths.remove(path)
        history_paths.insert(0, path)

        with open(self.history_file, "w", encoding="utf-8") as f:
            for p in history_paths[:50]:
                f.write(p + "\n")
        self.load_history()

    def load_history(self):
        self.hist_list.clear()
        for path in self.get_history_paths():
            if os.path.exists(path):
                self.add_item_to_list(self.hist_list, path)

    def get_history_paths(self):
        if not os.path.exists(self.history_file): return []
        with open(self.history_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    # دالة مسح الهستوري
    def clear_history(self):
        self.hist_list.clear()
        if os.path.exists(self.history_file):
            open(self.history_file, 'w').close()


if __name__ == "__main__":
    import time
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QSplashScreen

    app = QApplication(sys.argv)

    # هنا السر: تصغير البانر لـ 600 بيكسل مع الحفاظ على الدقة
    splash_pix = QPixmap("bannar.png").scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    time.sleep(2)
    window = SaberApp()
    window.show()
    splash.finish(window)
    sys.exit(app.exec())