import requests
from bs4 import BeautifulSoup
import json


# Define the channel username and desired manga
channel_user = "AWManga"
manga_name = "second life ranker"

def search_manga_links(channel_user, manga_name, last_episode):
    manga_data = []

    for episode in range(last_episode, 0, -1):
        try:
            query = f"{manga_name} {episode}.zip"
            search_url = f"https://t.me/s/{channel_user}?q={query}"
            print(f"[DEBUG] Searching for episode {episode} at URL: {search_url}")
            response = requests.get(search_url)

            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch search results for episode {episode}. Status Code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")

            if not messages:
                print(f"[DEBUG] No messages found for episode {episode}.")
                continue

            for index, message in enumerate(messages):
                try:
                    # Log full message for debugging
                    #print(f"[DEBUG] Full message content: {message.prettify()}")

                    # Extract message text
                    message_text = message.find("div", class_="tgme_widget_message_text")
                    text_content = message_text.get_text(strip=True) if message_text else ""
                    print(f"[DEBUG] Message text: {text_content}")

                    if "#Tower_Of_God" in text_content or manga_name.lower() in text_content.lower():
                        # Extract file link
                        file_div = message.find("div", class_="tgme_widget_message_document_title")
                        if file_div:
                            file_name = file_div.get_text(strip=True)
                            print(f"[DEBUG] File name: {file_name}")

                            link_tag = message.find("a", class_="tgme_widget_message_document_wrap")
                            if link_tag:
                                message_link = link_tag["href"]
                                print(f"[DEBUG] File link: {message_link}")

                                manga_data.append({
                                    "manga": manga_name,
                                    "link": message_link,
                                    "episond": str(episode)
                                })

                                print(f"[INFO] Found episode {episode}: {file_name} - {message_link}")
                except Exception as inner_e:
                    print(f"[ERROR] Error processing message for episode {episode}: {inner_e}")
        except Exception as e:
            print(f"[ERROR] Error processing episode {episode}: {e}")

    print(f"[DEBUG] Total episodes found: {len(manga_data)}")
    return manga_data

if __name__ == "__main__":
    last_episode = 193

    print(f"Searching for episodes of manga '{manga_name}' in channel @{channel_user}...")
    manga_links = search_manga_links(channel_user, manga_name, last_episode)

    output_file = f"{manga_name.replace(' ', '_').lower()}_links.json"
    if manga_links:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(manga_links, f, ensure_ascii=False, indent=4)
        print(f"Search complete! Links saved to {output_file}")
    else:
        print(f"[INFO] No links found. JSON file not created.")
