# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QDesktopWidget, QPushButton, QLineEdit, QGridLayout, QTextEdit
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import configparser
import re
from selenium.webdriver.common.keys import Keys
import pyperclip
import keyboard


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.driver = None
        self.is_running = False
        self.loop_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.loop_process)
        self.initUI()
        self.setup_hotkeys()

    def initUI(self):
        self.setWindowTitle('DC 갤러리 글쓰기 (F1: 시작, F2: 중지)')
        self.setGeometry(300, 300, 500, 400)
        
        layout = QGridLayout()
        
        # URL 입력
        url_label = QLabel('DC URL 입력:', self)
        self.url_entry = QLineEdit(self)
        layout.addWidget(url_label, 0, 0)
        layout.addWidget(self.url_entry, 0, 1)
        
        # 아이디 입력
        id_label = QLabel('아이디:', self)
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("아이디를 입력하세요")
        layout.addWidget(id_label, 1, 0)
        layout.addWidget(self.id_input, 1, 1)
        
        # 비밀번호 입력
        pw_label = QLabel('비밀번호:', self)
        self.pw_input = QLineEdit(self)
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("비밀번호를 입력하세요")
        layout.addWidget(pw_label, 2, 0)
        layout.addWidget(self.pw_input, 2, 1)
        
        # 제목 입력
        title_label = QLabel('제목:', self)
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("제목을 입력하세요")
        layout.addWidget(title_label, 3, 0)
        layout.addWidget(self.title_input, 3, 1)
        
        # 이미지 URL 입력
        imgurl_label = QLabel('이미지 URL:', self)
        self.imgurl_input = QLineEdit(self)
        self.imgurl_input.setPlaceholderText("이미지 URL을 입력하세요")
        layout.addWidget(imgurl_label, 4, 0)
        layout.addWidget(self.imgurl_input, 4, 1)
        
        # 내용 입력
        content_label = QLabel('내용:', self)
        self.content_input = QTextEdit(self)
        self.content_input.setPlaceholderText("본문 내용을 입력하세요")
        layout.addWidget(content_label, 5, 0)
        layout.addWidget(self.content_input, 5, 1)
        
        # 쿨타임 입력
        cooldown_label = QLabel('쿨타임(초):', self)
        self.cooldown_input = QLineEdit(self)
        self.cooldown_input.setPlaceholderText("반복 간격(초)을 입력하세요")
        layout.addWidget(cooldown_label, 6, 0)
        layout.addWidget(self.cooldown_input, 6, 1)
        
        # 중첩 키워드 입력
        keyword_label = QLabel('중첩 키워드:', self)
        self.keyword_input = QLineEdit(self)
        self.keyword_input.setPlaceholderText("중첩할 키워드를 입력하세요 (예: .)")
        layout.addWidget(keyword_label, 7, 0)
        layout.addWidget(self.keyword_input, 7, 1)
        
        # 상태 표시
        self.status_label = QLabel('상태: 대기 중 (F1: 시작, F2: 중지)', self)
        layout.addWidget(self.status_label, 8, 0, 1, 2)
        
        self.setLayout(layout)
        self.center()
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def setup_hotkeys(self):
        keyboard.on_press_key('F1', lambda _: self.start_process())
        keyboard.on_press_key('F2', lambda _: self.stop_process())
        
    def start_process(self):
        if not self.is_running:
            self.is_running = True
            self.loop_count = 0
            print("프로세스 시작됨")
            self.status_label.setText('상태: 실행 중 (F1: 시작, F2: 중지)')
            # 모든 입력창 비활성화
            self.url_entry.setEnabled(False)
            self.id_input.setEnabled(False)
            self.pw_input.setEnabled(False)
            self.title_input.setEnabled(False)
            self.imgurl_input.setEnabled(False)
            self.content_input.setEnabled(False)
            self.cooldown_input.setEnabled(False)
            self.keyword_input.setEnabled(False)
            self.submit_url()
        else:
            print("이미 실행 중입니다.")
        
    def stop_process(self):
        if self.is_running:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.timer.stop()
            self.is_running = False
            self.loop_count = 0
            self.status_label.setText('상태: 대기 중 (F1: 시작, F2: 중지)')
            # 모든 입력창 다시 활성화
            self.url_entry.setEnabled(True)
            self.id_input.setEnabled(True)
            self.pw_input.setEnabled(True)
            self.title_input.setEnabled(True)
            self.imgurl_input.setEnabled(True)
            self.content_input.setEnabled(True)
            self.cooldown_input.setEnabled(True)
            self.keyword_input.setEnabled(True)
            print("프로세스 중지됨")
        else:
            print("이미 중지된 상태입니다.")
    
    def loop_process(self):
        if self.is_running:
            # 메인 스레드에서 실행
            QTimer.singleShot(0, self.submit_url)
        else:
            self.timer.stop()
        
    def submit_url(self):
        url = self.url_entry.text()
        id_text = self.id_input.text()
        pw_text = self.pw_input.text()
        title_text = self.title_input.text()
        imgurl_text = self.imgurl_input.text()
        content_text = self.content_input.toPlainText()
        cooldown_text = self.cooldown_input.text()
        keyword_text = self.keyword_input.text()
        
        # 중첩 키워드 적용
        if keyword_text:
            title_text = title_text + (keyword_text * self.loop_count)
            content_text = content_text + (keyword_text * self.loop_count)
        
        if url and id_text and pw_text and title_text:
            # 비밀번호 4자 이상 체크
            if len(pw_text) < 4:
                print("비밀번호는 4자 이상이어야 합니다.")
                self.is_running = False
                self.status_label.setText('상태: 대기 중 (F1: 시작, F2: 중지)')
                return
            
            # 내용 2자 이상 체크
            if len(content_text) < 2:
                print("내용은 2자 이상이어야 합니다.")
                self.is_running = False
                self.status_label.setText('상태: 대기 중 (F1: 시작, F2: 중지)')
                return
            # 이미 드라이버가 있고 같은 URL에 있는지 확인
            if self.driver and self.driver.current_url == url:
                print("이미 같은 페이지에 있습니다. 글쓰기 페이지로 이동합니다.")
                current_url = self.driver.current_url
                match = re.search(r"id=([\w-]+)", current_url)
                if match:
                    gall_id = match.group(1)
                    write_url = f"https://gall.dcinside.com/mgallery/board/write/?id={gall_id}"
                    self.driver.get(write_url)
                    time.sleep(3)
                else:
                    print("갤러리 ID를 찾을 수 없습니다.")
                    self.is_running = False
                    self.status_label.setText('상태: 대기 중 (F1: 시작, F2: 중지)')
                    return
            else:
                # 새로운 드라이버 생성
                if self.driver:
                    self.driver.quit()
                chrome_options = Options()
                chrome_options.add_argument("--start-maximized")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # 먼저 입력받은 URL로 이동
                self.driver.get(url)
            
            # 현재 페이지 URL에서 id 추출
            current_url = self.driver.current_url
            match = re.search(r"id=([\w-]+)", current_url)
            
            if match:
                gall_id = match.group(1)
                write_url = f"https://gall.dcinside.com/mgallery/board/write/?id={gall_id}"
                print(f"갤러리 ID: {gall_id}")
                print(f"글쓰기 페이지로 이동: {write_url}")
                self.driver.get(write_url)
                
                # 페이지 로딩 대기
                time.sleep(3)
                
                # 아이디 입력
                try:
                    id_field = self.driver.find_element(By.ID, 'name')
                    id_field.click()
                    time.sleep(0.5)
                    id_field.clear()
                    id_field.send_keys(id_text)
                    print("아이디 입력 완료")
                except Exception as e:
                    print(f"아이디 입력 중 오류: {e}")
                
                # 비밀번호 입력
                try:
                    password_field = None
                    try:
                        password_field = self.driver.find_element(By.NAME, 'password')
                    except:
                        pass
                    if not password_field:
                        try:
                            password_field = self.driver.find_element(By.ID, 'password')
                        except:
                            pass
                    if not password_field:
                        try:
                            password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                        except:
                            pass
                    if password_field:
                        password_field.click()
                        time.sleep(0.5)
                        password_field.clear()
                        password_field.send_keys(pw_text)
                        print("비밀번호 입력 완료")
                    else:
                        print("비밀번호 필드를 찾을 수 없습니다.")
                except Exception as e:
                    print(f"비밀번호 입력 중 오류: {e}")
                
                # 제목 입력
                try:
                    subject_field = self.driver.find_element(By.ID, 'subject')
                    subject_field.click()
                    time.sleep(0.5)
                    subject_field.clear()
                    subject_field.send_keys(title_text)
                    print("제목 입력 완료")
                except Exception as e:
                    print(f"제목 입력 중 오류: {e}")
                
                # 이미지 URL, 내용 입력
                try:
                    editable_div = self.driver.find_element(By.CSS_SELECTOR, 'div.note-editable[contenteditable="true"]')
                    editable_div.click()
                    time.sleep(0.5)
                    if imgurl_text:
                        # HTML 체크박스 클릭
                        try:
                            html_checkbox = self.driver.find_element(By.ID, 'chk_html')
                            if not html_checkbox.is_selected():
                                html_checkbox.click()
                                time.sleep(0.5)
                                print("HTML 체크박스 클릭 완료")
                        except Exception as e:
                            print(f"HTML 체크박스 클릭 중 오류: {e}")
                        
                        # textarea에서 이미지 태그 입력
                        try:
                            textarea = self.driver.find_element(By.CSS_SELECTOR, 'textarea.note-codable')
                            textarea.clear()
                            img_tag = f'<p><img src="{imgurl_text}"></p>'
                            textarea.send_keys(img_tag)
                            print("textarea에 이미지 태그 입력 완료")
                        except Exception as e:
                            print(f"textarea 이미지 태그 입력 중 오류: {e}")
                        
                        # HTML 체크박스 다시 클릭 (해제)
                        try:
                            html_checkbox = self.driver.find_element(By.ID, 'chk_html')
                            if html_checkbox.is_selected():
                                html_checkbox.click()
                                time.sleep(0.5)
                                print("HTML 체크박스 해제 완료")
                        except Exception as e:
                            print(f"HTML 체크박스 해제 중 오류: {e}")
                    if content_text:
                        editable_div.send_keys(content_text)
                        print("본문 내용 입력 완료")
                except Exception as e:
                    print(f"이미지 URL/내용 입력 중 오류: {e}")
                
                # 등록 버튼 클릭
                try:
                    time.sleep(3)  # 3초 대기
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn_blue.btn_svc.write[type="image"]')
                    submit_button.click()
                    print("등록 버튼 클릭 완료")
                    time.sleep(2)
                except Exception as e:
                    print(f"등록 버튼 클릭 중 오류: {e}")
                
                # 쿨타임 설정 및 다음 루프 준비
                if cooldown_text and cooldown_text.isdigit() and self.is_running:
                    cooldown_seconds = int(cooldown_text) * 1000  # 밀리초로 변환
                    self.loop_count += 1
                    print(f"루프 {self.loop_count} 완료. {cooldown_seconds/1000}초 후 다음 루프 시작")
                    # 메인 스레드에서 타이머 시작
                    QTimer.singleShot(0, lambda: self.timer.start(cooldown_seconds))
                else:
                    self.is_running = False
                    self.timer.stop()
                    self.status_label.setText('상태: 대기 중 (F1: 시작, F2: 중지)')
                    print("작업 완료. F1을 눌러 다시 시작하거나 F2를 눌러 종료하세요.")
            else:
                print("갤러리 ID를 찾을 수 없습니다.")
                self.is_running = False
        else:
            print("모든 필드를 입력해주세요.")
            self.is_running = False
            self.status_label.setText('상태: 대기 중 (F1: 시작, F2: 중지)')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
