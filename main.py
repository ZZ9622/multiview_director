import sys
import cv2
import numpy as np
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QFrame, QListWidget, 
                             QSizePolicy, QSplitter, QProgressBar, QGroupBox)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

class AudioMeter(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setOrientation(Qt.Orientation.Vertical)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setFixedWidth(4)
        self.setStyleSheet("QProgressBar { border: 1px solid #222; background: #000; } QProgressBar::chunk { background: #00FF00; }")

class CameraWidget(QWidget):
    clicked = pyqtSignal(int, str)

    def __init__(self, cam_id, label_text="CAM", is_main=False):
        super().__init__()
        self.cam_id = cam_id
        self.label_text = label_text
        self.is_main = is_main
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        
        # 主画面使用红色边框，小画面灰色
        color = "#FF0000" if is_main else "#333"
        self.video_label.setStyleSheet(f"background-color: #000; border: 2px solid {color};")
        
        self.audio_meter = AudioMeter()
        layout.addWidget(self.audio_meter)
        layout.addWidget(self.video_label, stretch=1)

    def mousePressEvent(self, event):
        if not self.is_main:
            self.clicked.emit(self.cam_id, self.label_text)

    def update_frame(self, frame_count, display_name=None):
        target_size = self.video_label.size()
        w, h = max(target_size.width(), 10), max(target_size.height(), 10)
        
        img = np.zeros((h, w, 3), dtype=np.uint8)
        name = display_name if display_name else self.label_text
        
        cv2.putText(img, name, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6 if self.is_main else 0.4, (0, 255, 0), 1)
        
        # 扫描线效果
        line_y = (frame_count * 4) % h
        cv2.line(img, (0, line_y), (w, line_y), (25, 25, 25), 1)

        qt_img = QImage(img.data, w, h, w*3, QImage.Format.Format_RGB888).rgbSwapped()
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))
        self.audio_meter.setValue(random.randint(40, 60))

class BasketballDirectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Basketball Production - Refined Layout")
        self.setGeometry(50, 50, 1920, 850)
        self.setStyleSheet("background-color: #050505; color: #eee;")

        self.current_source_name = "CAM 0"
        self.current_source_id = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 1. 全局水平分割器 (左 4 : 右 6)
        self.global_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ================= 左侧区域：生产控制 (40%) =================
        left_area = QWidget()
        left_v_layout = QVBoxLayout(left_area)
        left_v_layout.setContentsMargins(0, 0, 0, 0)

        # 左上：PROGRAM
        self.program_view = CameraWidget(999, "PROGRAM: CAM 0", is_main=True)
        left_v_layout.addWidget(self.program_view, stretch=4)

        # 左下：3x3 矩阵
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(2)
        self.cams = []
        for i in range(9):
            name = f"CAM {i}" if i < 8 else "SCORE BOARD"
            cam = CameraWidget(i, name)
            cam.clicked.connect(self.handle_switch)
            grid_layout.addWidget(cam, i // 3, i % 3)
            self.cams.append(cam)
        left_v_layout.addWidget(grid_container, stretch=6)

        # ================= 右侧区域：AI 功能区 (60%) =================
        right_area = QWidget()
        right_v_layout = QVBoxLayout(right_area)
        
        # 右侧上方：AI LOG 对话框
        self.ai_log_group = QGroupBox("AI LOG")
        self.ai_log_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        ai_log_layout = QVBoxLayout(self.ai_log_group)
        
        self.log_list = QListWidget()
        self.log_list.setStyleSheet("background: #000; color: #00FF00; border: none; font-family: Monospace; font-size: 12px;")
        ai_log_layout.addWidget(self.log_list)
        
        # 限制 AI LOG 的初始高度，让它看起来“小一点”
        self.ai_log_group.setFixedHeight(300)
        right_v_layout.addWidget(self.ai_log_group)

        # 右侧下方：预留拓展空间 (留白)
        self.expansion_area = QFrame()
        self.expansion_area.setStyleSheet("background: transparent; border: 1px dashed #333;")
        right_v_layout.addWidget(self.expansion_area, stretch=1)

        # 加入分割器并分配比例
        self.global_splitter.addWidget(left_area)
        self.global_splitter.addWidget(right_area)
        self.global_splitter.setSizes([640, 960]) # 4:6
        
        main_layout.addWidget(self.global_splitter)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(33)
        self.frame_count = 0

    def handle_switch(self, cam_id, name):
        self.current_source_id = cam_id
        self.current_source_name = name
        self.log_list.addItem(f"> SYSTEM: Master output switched to {name}")
        self.log_list.scrollToBottom()

    def update_ui(self):
        self.frame_count += 1
        self.program_view.update_frame(self.frame_count, display_name=f"PROGRAM: {self.current_source_name}")
        for c in self.cams:
            c.update_frame(self.frame_count)
        
        # 模拟 AI 检测日志
        if self.frame_count % 300 == 0:
            events = ["3-PT SHOT", "TURNOVER", "FAST BREAK"]
            self.log_list.addItem(f"[AI] {random.choice(events)} DETECTED (CAM {random.randint(0,7)})")
            self.log_list.scrollToBottom()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BasketballDirectorApp()
    window.show()
    sys.exit(app.exec())