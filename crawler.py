from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
import time

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("window-size=400,1200")
chrome_options.add_argument("--headless")

chromedriver_path = ChromeDriverManager().install()
driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)


 
def crawler_main(url):
    driver.get(url)
    
    # 맨 아래로 스크롤
    scroll_pause_time = 2 # 줄이면 성능 안좋아짐
    last = driver.execute_script("return document.documentElement.scrollHeight")
    html = []
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_point = driver.execute_script("return document.documentElement.scrollHeight")
        if new_point == last:
            break
        last = new_point

    # 버튼
    buttons = driver.find_elements(By.CSS_SELECTOR, '#more-replies > yt-button-shape > button > yt-touch-feedback-shape > div > div.yt-spec-touch-feedback-shape__fill')
    for button in buttons:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(1) #바꾸면 성능 하락
        ActionChains(driver).move_to_element(button).click(button).perform()
        time.sleep(1)

    # 최종 페이지 파싱
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    data = []

    comment_threads = soup.select('ytd-comment-thread-renderer')
    for thread in comment_threads:
        # 원본 추출
        id = thread.select_one('#author-text').text.strip()
        cotent = thread.select_one('#content-text').text.strip()
        
        # 답글 추출
        replies = []
        reply_id = thread.select('#replies #author-text')
        for author in reply_id:
            reply_id = author.text.strip()
        reply_cotents = thread.select('#replies #content-text')
        for content in reply_cotents:
            reply_cotents = content.text.strip()
            replies.append({
                'reply_id': reply_id,
                'reply_comment': reply_cotents
            })
            
        document = {
            'original_id': id,
            'original_comment': cotent,
            'replies': replies
        }
        data.append(document)

 

    driver.quit()
    return data
