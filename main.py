import sys
import json
import pandas as pd
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor

from crawler import crawler_main
import time

def format_json(json_data):
    data = json.loads(json_data)
    total_comments = sum(len(item['replies']) + 1 for item in data)
    
    formatted_output = f"총 댓글 개수 {total_comments}개\n\n"
    
    for item in data:
        formatted_output += f"original_id: {item['original_id']}\n"
        formatted_output += f"original_comment: {item['original_comment']}\n"
        formatted_output += "replies:\n"
        for reply in item['replies']:
            formatted_output += f"  - {reply['reply_id']}: {reply['reply_comment']}\n"
        formatted_output += "\n"
    
    return formatted_output

class CrawlerThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)
    data_collected = pyqtSignal(list)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.is_paused = False
        self.data = []

    def run(self):
        try:
            self.progress.emit("해당 페이지 크롤링 시작")
            while not self.is_paused:
                new_data = crawler_main(self.url)
                self.data.extend(new_data)
                formatted_result = format_json(json.dumps(self.data, ensure_ascii=False))
                self.finished.emit(formatted_result)
                self.data_collected.emit(self.data)
                break
            while self.is_paused:
                time.sleep(1)
        except Exception as e:
            self.finished.emit(f"오류 발생: {e}")

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        self.run()

class Main(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.blinking = False
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        self.is_paused = False
        self.crawler_thread = None
        self.crawled_data = []

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.resize(500, 500)

        layout = QFormLayout()
        self.url = QLineEdit()
        self.console_label = QLabel("크롤결과")
        self.console = QTextEdit()
        
        self.url.setMinimumWidth(400)
        self.console.setStyleSheet("border: 1px solid grey; padding: 5px; background-color: white;")
        self.console.setMinimumHeight(400)
        self.console.setMinimumWidth(480)
        self.console.setReadOnly(True)

        self.crawl_button = QPushButton('크롤 시작')
        self.crawl_button.clicked.connect(self.start)

        self.pause_button = QPushButton('일시정지')
        self.pause_button.clicked.connect(self.pause_resume)
        self.pause_button.setEnabled(False)

        self.save_button = QPushButton('저장')
        self.save_button.clicked.connect(self.save)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.crawl_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.save_button)

        layout.addRow("URL링크:", self.url)
        layout.addRow(self.console_label)
        layout.addRow(self.console)
        main_layout.addLayout(layout)
        main_layout.addLayout(button_layout)        
        self.show()

    def start(self):
        url = self.url.text()
        
        if url:
            self.console.clear()
            self.blinking = True
            self.blink_timer.start(300)
            self.crawler_thread = CrawlerThread(url)
            self.crawler_thread.finished.connect(self.crawler_finish)
            self.crawler_thread.progress.connect(self.update_console)
            self.crawler_thread.data_collected.connect(self.temporary)
            self.crawler_thread.start()
            self.crawl_button.setEnabled(False)
            self.pause_button.setEnabled(True)

    def crawler_finish(self, result):
        self.update_console(result)
        self.blinking = False
        self.blink_timer.stop()
        self.crawl_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.console.moveCursor(QTextCursor.Start)


    def update_console(self, message):
        self.console.append(message)

    def blink(self):
        if self.blinking:
            current_color = self.crawl_button.palette().button().color().name()
            new_color = "#a8abb6" if current_color == "#82858f" else "#82858f"
            self.crawl_button.setStyleSheet(f"background-color: {new_color};")

    def pause_resume(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            if not self.is_paused:
                self.crawler_thread.pause()
                self.pause_button.setText("재개")
                self.update_console("크롤러가 일시정지되었습니다.")
                self.is_paused = True
            else:
                self.crawler_thread.resume()
                self.pause_button.setText("일시정지")
                self.update_console("크롤러가 재개되었습니다.")
                self.is_paused = False

    def temporary(self, data):
        self.crawled_data.extend(data)

    def save(self):
        try:
            if self.crawled_data:
                df = pd.DataFrame(self.crawled_data)
                df.to_json('result.json', orient='records', force_ascii=False, indent=4)
                self.update_console("데이터가 저장되었습니다.")
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("저장되었습니다.")
                msg.setWindowTitle("알림")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.buttonClicked.connect(self.reset_ui)
                msg.exec_()
            else:
                self.update_console("저장할 데이터가 없습니다.")
        except Exception as e:
            self.update_console(f"저장 중 오류 발생: {e}")

    def reset_ui(self):
        self.url.clear()
        self.console.clear()
        self.crawled_data = []
        self.crawl_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("일시정지")
        self.is_paused = False
        self.blinking = False
        self.blink_timer.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
