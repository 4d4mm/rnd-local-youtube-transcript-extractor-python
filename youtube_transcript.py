import time
import random
from typing import List, Dict
import re 

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class YouTubeSearchTranscript:
    def __init__(self, headless: bool = False):
        """Initialize WebDriver with YouTube-specific configurations."""
        chrome_options = Options()
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Stealth modifications
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)
    
    def _accept_cookies(self) -> None:
        """Handle YouTube cookie consent popup."""
        try:
            # Wait for and click accept cookies button
            cookie_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Accept')]"))
            )
            cookie_button.click()
            time.sleep(random.uniform(1, 2))
        except:
            print("No cookie popup or unable to click")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search YouTube and extract video details including transcripts.
        
        :param query: Search query
        :param max_results: Maximum number of results to process
        :return: List of video details with transcripts
        """
        # Navigate to YouTube
        self.driver.get('https://www.youtube.com')
        
        # Handle cookies
        self._accept_cookies()
        
        # Find search box and perform search
        search_box = self.driver.find_element(By.NAME, 'search_query')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        # Wait for search results
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'video-title'))
        )
        
        # Find video links
        video_links = self.driver.find_elements(By.ID, 'video-title')[:max_results]
        
        video_details = []
        for link in video_links:
            try:
                # Open video in new tab
                link.send_keys(Keys.CONTROL + Keys.RETURN)
                
                # Switch to new tab
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # Wait for video to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'title'))
                )
                
                # Extract basic video details
                title = self.driver.find_element(By.CLASS_NAME, 'title').text
                
                # Attempt to get transcript
                transcript = self._extract_transcript()
                
                video_details.append({
                    'title': title,
                    'url': self.driver.current_url,
                    'transcript': transcript
                })
                
                # Close tab and switch back
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"Error processing video: {e}")
        
        return video_details
    
    def _extract_transcript(self) -> str:
        """
        Extract video transcript.
        
        Note: This method might require more robust implementation 
        due to YouTube's dynamic transcript loading.
        """
        try:
            # mute the video    
            mute = WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.ytp-mute-button'))
            )
            mute.click()

            # Open transcript menu
            more_actions = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='expand']"))
            )
            more_actions.click()
            
            # Open transcript option
            transcript_option = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Show transcript']"))
            )
            transcript_option.click()

            
            # Wait for transcript to load
            transcript_elements = WebDriverWait(self.driver, 100).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ytd-transcript-segment-list-renderer>*"))
            )
            md_transcript = []
            for el in transcript_elements:
                if el.tag_name == 'ytd-transcript-section-header-renderer':
                    md_transcript.append(
                        f"# {el.get_attribute("textContent").strip()}"
                    )    
                else:
                    transcript_line = el.get_attribute("textContent")
                    transcript_line_no_ts = re.sub(r"(\s+(?:\d{2}:)?\d{2}:\d{2}\s+)", r"", transcript_line)
                    md_transcript.append(
                        transcript_line_no_ts.strip()
                    )

            # Combine transcript text
            transcript = '\n'.join(md_transcript)
            
            return transcript
        except Exception as e:
            print(f"Transcript extraction failed: {e}")
            return ""
    
    def close(self):
        """Close the browser."""
        self.driver.quit()

def main():
    yt_search = YouTubeSearchTranscript(headless=False)
    try:
        results = yt_search.search("Python programming", max_results=3)
        for video in results:
            print(f"Title: {video['title']}")
            print(f"URL: {video['url']}")
            print(f"Transcript: {video['transcript']}")
            print("---")
    finally:
        yt_search.close()

if __name__ == '__main__':
    main()