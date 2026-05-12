import datetime
import json
import os
import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientError

from typing import Dict, Any, List

REQ_URL = 'https://oc.sjtu.edu.cn/api/v1'

with open('./COOKIE.TXT', 'r') as f:
    cookie = f.read().strip()

headers = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0'
}

def parse_iso_datetime(iso_str: str, to_str: bool = False) -> datetime.datetime | str | None:
    if iso_str is None:
        return None
    try:
        dt = datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        if to_str:
            return dt.strftime("%Y-%m-%d_%H:%M:%S")
        return dt
    except TypeError:
        return None
    
def get_name_by_id(cards: List[Dict[str, Any]], id: int) -> str:
    for card in cards:
        if card.get('id') == id:
            return card.get('name', 'Unknown')
    return 'Unknown'

def get_value_by_id(cards: List[Dict[str, Any]], id: int, key: str) -> Any | bool:
    for card in cards:
        if card.get('id') == id:
            return card.get(key)
    return False

async def fetch_all_cards(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    retries = 2
    for attempt in range(retries + 1):
        try:
            timeout = ClientTimeout(total=10)
            async with session.get(url, timeout=timeout, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                return {
                    "url": url,
                    "status": response.status,
                    "data": data,
                    "error": None
                }
        except ClientError as e:
            error_msg = f"HTTP Error: {e}"
        except asyncio.TimeoutError:
            error_msg = f" (Attempting {attempt+1}/{retries+1})"
        except Exception as e:
            error_msg = f"Raised: {type(e).__name__} - {e}"
        

        if attempt == retries:
            return {
                "url": url,
                "status": None,
                "data": None,
                "error": error_msg
            }

        await asyncio.sleep(0.5 * (attempt + 1))

    return {"url": url, "error": "未知错误"}

async def fetch_all(urls: List[str]) -> List[Dict[str, Any]]:
    """
    并发请求多个 API, 使用连接池优化. 
    """
    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_all_cards(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

async def request_base_cards(save_to_file: bool = True) -> List[Dict[str, Any]]:
    base_url = [f"{REQ_URL}/dashboard/dashboard_cards"]
    card_response = await fetch_all(base_url)
    task_cards = card_response[0]
    if task_cards.get('error'):
        print(f"Error fetching cards at {base_url[0]}: {task_cards['error']}")
        return []
    else:
        print(f"Fetched cards at {base_url[0]}, status: {task_cards['status']}")
        processed = []
        for c in task_cards['data']:
            processed.append({
                "name": c.get('shortName'),
                "id": c.get('id'),
            })

        if save_to_file:
            with open('tasks_card.json', 'w', encoding="utf-8") as f:
                json.dump(processed, f, indent=4, ensure_ascii=False)
        return processed

async def request_detailed(save_to_file: bool = True) -> List[Dict[str, Any]]:
    cards = await request_base_cards(save_to_file=False)
    if not cards:
        print("No cards to fetch details for.")
        return []
    
    if len(cards) == 0:
        print("No cards found in the base request.")
        return []
    
    appendix = "?exclude_assignment_submission_types%5B%5D=wiki_page&exclude_response_fields%5B%5D=description&exclude_response_fields%5B%5D=rubric&include%5B%5D=assignments&include%5B%5D=discussion_topic&override_assignment_dates=true&per_page=50"
    urls = [f"{REQ_URL}/courses/{card['id']}/assignment_groups{appendix}" for card in cards]
    detailed_results = await fetch_all(urls)

    processed = []

    flag = os.path.exists('tasks.json')

    if flag:
        with open('tasks.json', 'r', encoding='utf-8') as f:
            existing_tasks = json.load(f)
    
    for res in detailed_results:
        if res.get('error'):
            print(f"Error fetching details at {res['url']}: {res['error']}")
        else:
            print(f"Fetched details at {res['url'][:40]}..., status: {res['status']}")
            tasks_1 = res['data']
            for t1 in tasks_1:
                t1_name = t1.get('name', 'Unknown')
                tasks_2 = t1.get('assignments', [])
                for t2 in tasks_2:
                    t2_name = t2.get('name', 'Unknown')
                    id = t2.get('id')
                    course_id = t2.get('course_id')
                    due_at = t2.get('due_at')
                    unlock_at = t2.get('unlock_at')
                    lock_at = t2.get('lock_at')
                    lock_explanation = t2.get('lock_explanation')
                    html_url = t2.get('html_url')
                    #print(f"received due at: {due_at} with type {type(due_at)}")
                    if lock_at:
                        lock_at_datetime = parse_iso_datetime(lock_at)
                        if lock_at_datetime and lock_at_datetime < datetime.datetime.now():
                            continue
                    if due_at:
                        due_at_datetime = parse_iso_datetime(due_at)
                        if due_at_datetime and due_at_datetime < datetime.datetime.now():
                            continue

                    info_dict = {
                        "course_name": get_name_by_id(cards, course_id),
                        "assignment_group_name": t1_name,
                        "assignment_name": t2_name,
                        "course_id": course_id,
                        "assignment_id": id,
                        "due_at": parse_iso_datetime(due_at, to_str=True) if due_at else None,
                        "unlock_at": parse_iso_datetime(unlock_at, to_str=True) if unlock_at else None,
                        "lock_at": parse_iso_datetime(lock_at, to_str=True) if lock_at else None,
                        "explanation": lock_explanation,
                        "from": "canvas",
                        "to": "canvas_notification",
                        "url": html_url,
                        "zombie": get_value_by_id(existing_tasks, id, "zombie") if flag else False,
                        "complete": get_value_by_id(existing_tasks, id, "complete") if flag else False
                    }
                    processed.append(info_dict)

    if save_to_file:
        with open('tasks.json', 'w', encoding="utf-8") as f:
            json.dump(processed, f, indent=4, ensure_ascii=False)
    
    return processed

async def main():
    await request_detailed(save_to_file=True)

if __name__ == "__main__":
    asyncio.run(main())