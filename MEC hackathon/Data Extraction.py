import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup

url = "https://www.khanacademy.org/math/algebra"
videos_dict = {}

def scrape_topic_data(url) :
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(15)

    try:
        accept_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All Cookies')]"))
        )
        accept_cookies_button.click()
        print("Cookies accepted.")
    except Exception as e:
        print("No cookie popup found or error:", str(e))

    video_links = driver.find_elements(By.CSS_SELECTOR, 'a._dwmetq')
    print(f"Number of video links: {len(video_links)}")

    video_data = [{'title': link.text.strip(), 'href': link.get_attribute('href')} for link in video_links]

    for video in video_data[1::]:
        video_title = video['title']
        video_href = video['href']

        print(f"Visiting: {video_href}")

        try:
            driver.get(video_href)
            driver.implicitly_wait(10)

            driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(5)

            try:
                print("Looking for Transcript tab...")
                transcript_tab = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='videoTabTranscript']"))
                )
                driver.execute_script("arguments[0].click();", transcript_tab)
                print("Transcript tab clicked!")
                time.sleep(5)
            except Exception as e:
                print(f"Error finding Transcript tab for {video_title}: {str(e)}")
                continue

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            transcript_items = soup.find_all('button', class_='_y8368zt')

            if transcript_items:
                transcript_lines = [item.text.strip() for item in transcript_items]

                videos_dict[video_title] = {
                    'video_url': video_href,
                    'transcript': transcript_lines
                }
                print(f"Transcript collected for: {video_title}")
            else:
                print(f"No transcript found for: {video_title}")

        except Exception as e:
            print(f"Error for {video_title}: {str(e)}")
            continue

    with open("transcripts.json", "w") as outfile:
        json.dump(videos_dict, outfile, indent=4)

    driver.quit()

scrape_topic_data(url)
