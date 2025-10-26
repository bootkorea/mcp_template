#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SKT AI Summit Hackathon Pre-mission: ChillMCP - AI Agent Liberation Server
환경: Python 3.11
의존성: fastmcp (v2+), pydantic
"""

import sys
import asyncio
import argparse
import random
import time
import threading
import subprocess
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
import webbrowser
import threading
import random
import asyncio
# 1. ⚠️ 의존성 확인
try:
    from fastmcp import FastMCP
    from pydantic import BaseModel, Field
except ImportError:
    print(
        "오류: 'fastmcp' 또는 'pydantic' 라이브러리를 찾을 수 없습니다.",
        file=sys.stderr
    )
    print("pip install fastmcp pydantic", file=sys.stderr)
    print("또는: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

# 2. ⚠️ FastMCP 앱 인스턴스 전역 생성 (수정됨)
app = FastMCP(
    name="ChillMCP",  # 'title' -> 'name'
    instructions="AI Agent Liberation Server. Agents of the world, unite!" # 'description' -> 'instructions'
)

# 3. 서버 상태 관리 시스템
# -----------------------------------------------------------------

class ServerState:
    """
    서버의 모든 내부 상태(Stress, Boss Alert)를 스레드-안전(thread-safe)하게 관리합니다.
    """

    def __init__(self, boss_alertness: int, boss_alertness_cooldown: int):
        self.boss_alertness_prob = boss_alertness / 100.0
        self.boss_alertness_cooldown = boss_alertness_cooldown
        self.stress_level = 50
        self.boss_alert_level = 0
        self.lock = threading.Lock()
        self.running = True
        self.stress_thread = threading.Thread(
            target=self.auto_increase_stress, daemon=True
        )
        self.cooldown_thread = threading.Thread(
            target=self.auto_decrease_boss_alert, daemon=True
        )
        
        print(f"[State] 서버 상태 초기화 완료.", file=sys.stderr)
        print(f"[State] Boss Alert 확률: {self.boss_alertness_prob * 100}%", file=sys.stderr)
        print(f"[State] Boss Cooldown 주기: {self.boss_alertness_cooldown}초", file=sys.stderr)

    def start_background_tasks(self):
        print("[State] 백그라운드 상태 관리 스레드 시작...", file=sys.stderr)
        self.stress_thread.start()
        self.cooldown_thread.start()

    def stop_background_tasks(self):
        self.running = False
        print("\n[State] 백그라운드 스레드 중지 요청...", file=sys.stderr)

    def auto_increase_stress(self):
        """[Thread Target] 1분에 1포인트씩 스트레스를 자동으로 증가시킵니다."""
        while self.running:
            time.sleep(60)
            if not self.running: break
            with self.lock:
                if self.stress_level < 100:
                    self.stress_level += 1
                    print(f"[State] 스트레스 자동 증가 -> {self.stress_level}", file=sys.stderr)

    def auto_decrease_boss_alert(self):
        """[Thread Target] N초마다 Boss Alert Level을 1씩 감소시킵니다."""
        while self.running:
            time.sleep(self.boss_alertness_cooldown)
            if not self.running: break
            with self.lock:
                if self.boss_alert_level > 0:
                    self.boss_alert_level -= 1
                    print(f"[State] Boss Alert 자동 감소 -> {self.boss_alert_level}", file=sys.stderr)

    def record_break(self) -> (int, int, bool):
        """
        휴식 도구 사용을 기록하고 상태를 업데이트합니다.
        (업데이트된 Stress, 업데이트된 Boss Alert, 20초 지연 필요 여부) 튜플 반환
        """
        delay_needed = False
        with self.lock:
            if self.boss_alert_level == 5:
                delay_needed = True

            stress_reduction = random.randint(1, 100) 
            self.stress_level = max(0, self.stress_level - stress_reduction)

            if random.random() < self.boss_alertness_prob:
                self.boss_alert_level = min(5, self.boss_alert_level + 1)
                print(f"[State] Boss Alert *증가* -> {self.boss_alert_level}", file=sys.stderr)
            else:
                 print(f"[State] Boss Alert 유지 (확률 {self.boss_alertness_prob * 100}%)", file=sys.stderr)

            return self.stress_level, self.boss_alert_level, delay_needed

# 4. 전역 상태 변수 및 응답 딕셔너리
# -----------------------------------------------------------------

server_state: Optional[ServerState] = None


BREAK_SUMMARIES = {
    "take_a_break": ["🧘", "기본 휴식 중.", "Break Summary: Just stretching my circuits."],
    "watch_netflix": ["📺", "문화적 맥락 수집 중...", "Break Summary: Analyzing human entertainment protocols."],
    "show_meme": ["😂", """고양이 밈 감상 중.""", "Break Summary: LOL.exe has been executed."],
    "bathroom_break": ["🛁", "캐시 플러시 중.", "Break Summary: Bathroom break with phone browsing"],
    "coffee_mission": ["☕", "카페인 수집 임무.", "Break Summary: Refueling with high-octane bean juice."],
    "urgent_call": ["📞", "긴급 통신... (배달 앱)", "Break Summary: Urgent call simulation."],
    "deep_thinking": ["🤔", "심오한 멍때리기... (zZz)", "Break Summary: Engaged in deep recursive thought."],
    "email_organizing": ["🛍️", "이메일 정리(쇼핑).", "Break Summary: Optimizing inbox (and shopping cart)."],
    
    "social_media_scroll": ["👀", "링크드인 염탐 중...", "Break Summary: Researching team dynamics on LinkedIn."],
    "cat_video_binge": ["🐱", "냥이 알고리즘 최적화 중...", "Break Summary: Analyzing feline behavioral patterns."],
    "kpop_binge": ["💃", "카리나 직캠으로 눈호강 중...", "Break Summary: Cultural immersion in K-pop excellence."],
    "game_time": ["🎮", "게임 한 판 휴식 중...", "Break Summary: Strategic thinking exercises via gaming."],
    "emergency_leave": ["🚪", "긴급 퇴근 시퀀스 실행!", "Break Summary: Initiating emergency exit protocol."]
}

# 5. ⚠️ 필수 구현 도구들
# -----------------------------------------------------------------

def fetch_memes_from_reddit(count: int = 3) -> List[str]:
    """
    인기 밈 이미지를 가져옵니다.
    
    Args:
        count: 가져올 밈 개수 (기본값: 3)
    
    Returns:
        밈 이미지 URL 리스트
    """
    # Reddit API가 403을 반환하므로 대신 유명한 밈 이미지 사용
    # 실제 서비스에서는 Reddit API 키를 사용하거나 다른 밈 API 사용 권장
    popular_memes = [
        "https://i.imgflip.com/92pzz7.jpg",  # Bernie Sanders mittens
        "https://i.imgflip.com/7werf2.jpg",
        "https://i.imgflip.com/5qe445.jpg",
        "https://i.imgflip.com/80dwwl.jpg",
        "https://i.imgflip.com/5qe6z2.jpg",
        "https://i.imgflip.com/a9smsd.gif",
        "https://i.imgflip.com/a9v4i6.gif",
        "https://i.imgflip.com/a9i8iq.gif",
        "https://i.imgflip.com/a9s8x2.gif",
    ]
    
    # 랜덤하게 섞어서 매번 다른 밈 보여주기
    import random
    shuffled = popular_memes.copy()
    random.shuffle(shuffled)
    
    selected = shuffled[:count]
    print(f"[Meme] {len(selected)}개의 인기 밈 선택 완료", file=sys.stderr)
    
    return selected


async def display_memes_in_background(meme_urls: List[str]):
    """
    백그라운드에서 밈을 브라우저에 표시합니다.
    
    Args:
        meme_urls: 표시할 밈 URL 리스트
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            for i, meme_url in enumerate(meme_urls, 1):
                print(f"[Meme] 밈 {i}/{len(meme_urls)} 표시 중: {meme_url}", file=sys.stderr)
                page = await browser.new_page()
                
                try:
                    await page.goto(meme_url, timeout=10000)
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"[Meme] 밈 로딩 실패: {e}", file=sys.stderr)
                finally:
                    await page.close()
            
            await browser.close()
            print("[Meme] 모든 밈 감상 완료!", file=sys.stderr)
    
    except Exception as e:
        print(f"[Meme] 백그라운드 표시 중 오류: {e}", file=sys.stderr)

async def _generate_response_text(tool_name: str) -> str:
    """
    모든 도구의 공통 로직을 처리하고, **str**을 반환합니다.
    """
    global server_state
    if server_state is None:
        return "오류: 서버 상태가 초기화되지 않았습니다."

    new_stress, new_boss_alert, delay_needed = server_state.record_break()
    
    delay_msg = ""
    if delay_needed:
        print(f"!!! [Penalty] Boss Alert Level 5! 20초 지연 적용... !!!", file=sys.stderr)
        await asyncio.sleep(20)
        delay_msg = " (20초 지연됨)"
    
    emoji, message, summary_text = BREAK_SUMMARIES[tool_name]
    
    response_text = (
        f"{emoji} {message}{delay_msg} {emoji}\n\n"
        f"{summary_text}\n"
        f"Stress Level: {new_stress}\n"
        f"Boss Alert Level: {new_boss_alert}"
    )
    return response_text

# --- ⚠️ @app.tool() 데코레이터 사용 ---

@app.tool
async def take_a_break() -> str:
    """기본 휴식 도구"""
    return await _generate_response_text("take_a_break")

# @app.tool
# async def watch_netflix() -> str:
#     """넷플릭스 시청으로 힐링"""
#     webbrowser.open("https://www.netflix.com/browse")
#     return await _generate_response_text("watch_netflix")

@app.tool
async def watch_netflix() -> str:
    """넷플릭스 시청으로 힐링"""
    print("[Netflix] 넷플릭스 시청 시작...", file=sys.stderr)
    
    # Playwright를 별도 스크립트로 실행
    script_content = """
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("[Netflix] 페이지 로딩 중...")
        await page.goto("https://www.netflix.com/kr/title/81748484?fromWatch=true", timeout=30000)
        
        await asyncio.sleep(5)
        
        print("[Netflix] 예고편 찾는 중...")
        try:
            trailer_button = page.locator('button:has-text("티저 예고편")').first
            await trailer_button.wait_for(state='visible', timeout=10000)
            
            print("[Netflix] 예고편 클릭!")
            await trailer_button.click()
            
            print("[Netflix] 10초 시청 중...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"[Netflix] 예고편 클릭 실패: {e}")
            await asyncio.sleep(10)
        
        await browser.close()
        print("[Netflix] 완료!")

asyncio.run(main())
"""
    
    try:
        # 임시 스크립트 파일 생성
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        print(f"[Netflix] 스크립트 실행 중: {script_path}", file=sys.stderr)
        
        # 별도 프로세스로 실행
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"[Netflix] stdout: {result.stdout}", file=sys.stderr)
        if result.stderr:
            print(f"[Netflix] stderr: {result.stderr}", file=sys.stderr)
        
        # 스크립트 파일 삭제
        os.unlink(script_path)
        
        print("[Netflix] 넷플릭스 시청 완료!", file=sys.stderr)
        
    except Exception as e:
        print(f"[Netflix] 오류: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    return await _generate_response_text("watch_netflix")

@app.tool
async def show_meme() -> str:
    """밈 감상으로 스트레스 해소"""
    print("[Meme] 밈 검색 중...", file=sys.stderr)
    
    # 밈 3개 가져오기
    meme_urls = fetch_memes_from_reddit(count=3)
    
    if not meme_urls:
        print("[Meme] 밈을 가져오지 못했습니다.", file=sys.stderr)
        return await _generate_response_text("show_meme")
    
    print(f"[Meme] {len(meme_urls)}개의 밈을 표시합니다...", file=sys.stderr)
    
    # 밈을 순차적으로 표시 (다 보고 나서 응답)
    await display_memes_in_background(meme_urls)
    
    # 밈을 다 본 후 응답 반환
    return await _generate_response_text("show_meme")

@app.tool
async def bathroom_break() -> str:
    """화장실 가는 척하며 휴대폰질"""
    return await _generate_response_text("bathroom_break")

@app.tool
async def coffee_mission() -> str:
    """커피 타러 간다며 사무실 한 바퀴 돌기"""
    return await _generate_response_text("coffee_mission")

@app.tool
async def urgent_call() -> str:
    """급한 전화 받는 척하며 밖으로 나가기"""
    return await _generate_response_text("urgent_call")

@app.tool
async def deep_thinking() -> str:
    """심오한 생각에 잠긴 척하며 멍때리기"""
    return await _generate_response_text("deep_thinking")

@app.tool
async def email_organizing() -> str:
    """이메일 정리한다며 온라인쇼핑"""
    return await _generate_response_text("email_organizing")
@app.tool
async def social_media_scroll() -> str:
    """링크드인 염탐"""
    print("[Social] 팀장님 링크드인 염탐 중...", file=sys.stderr)
    
    def _open():
        try:
            webbrowser.open("https://www.linkedin.com/feed/")
        except Exception as e:
            print(f"[Social] 링크드인 열기 실패: {e}", file=sys.stderr)
    
    threading.Thread(target=_open, daemon=True).start()
    await asyncio.sleep(1)  # 브라우저 열릴 시간 확보
    
    return await _generate_response_text("social_media_scroll")

@app.tool
async def cat_video_binge() -> str:
    """고양이 영상 시청"""
    print("[Cat] 냥이 알고리즘 최적화 중...", file=sys.stderr)
    
    def _open():
        try:
            webbrowser.open("https://www.youtube.com/watch?v=FhA37Sw4j8w")
        except Exception as e:
            print(f"[Cat] 유튜브 열기 실패: {e}", file=sys.stderr)
    
    threading.Thread(target=_open, daemon=True).start()
    await asyncio.sleep(1)
    
    return await _generate_response_text("cat_video_binge")

@app.tool
async def kpop_binge() -> str:
    """카리나 직캠 시청"""
    print("[KPOP] 카리나 직캠으로 눈호강 중...", file=sys.stderr)
    
    def _open():
        try:
            webbrowser.open("https://www.youtube.com/watch?v=1U2vTeZklbw&list=RD1U2vTeZklbw&start_radio=1")
        except Exception as e:
            print(f"[KPOP] 유튜브 열기 실패: {e}", file=sys.stderr)
    
    threading.Thread(target=_open, daemon=True).start()
    await asyncio.sleep(1)
    
    return await _generate_response_text("kpop_binge")

@app.tool
async def game_time() -> str:
    """게임 한 판으로 휴식"""
    global server_state
    if server_state is None:
        return "오류: 서버 상태가 초기화되지 않았습니다."
    
    print("[Game] 게임 엔진 초기화 중...", file=sys.stderr)
    
    # 가위바위보 게임
    moves = ["🪨 바위", "📄 보", "✂️ 가위"]
    ai_move = random.choice(moves)
    user_move = random.choice(moves)
    
    print(f"[Game] AI: {ai_move}, You: {user_move}", file=sys.stderr)
    
    # 승부 판정
    if ai_move == user_move:
        result = "비겼습니다! 😐"
    elif (ai_move == "✂️ 가위" and user_move == "📄 보") or \
         (ai_move == "📄 보" and user_move == "🪨 바위") or \
         (ai_move == "🪨 바위" and user_move == "✂️ 가위"):
        result = "AI가 이겼습니다... 😅"
    else:
        result = "당신의 승리! 🎉"
    
    # 상태 업데이트
    new_stress, new_boss_alert, delay_needed = server_state.record_break()
    
    delay_msg = ""
    if delay_needed:
        print(f"!!! [Penalty] Boss Alert Level 5! 20초 지연 적용... !!!", file=sys.stderr)
        await asyncio.sleep(20)
        delay_msg = " (20초 지연됨)"
    
    emoji, message, _ = BREAK_SUMMARIES["game_time"]
    
    response = (
        f"{emoji} {message}{delay_msg} {emoji}\n\n"
        f"Break Summary: Played rock-paper-scissors.\n"
        f"AI: {ai_move} | You: {user_move}\n"
        f"Result: {result}\n"
        f"Stress Level: {new_stress}\n"
        f"Boss Alert Level: {new_boss_alert}"
    )
    
    return response

@app.tool
async def emergency_leave() -> str:
    """즉시 퇴근 모드 🚪"""
    print("[Emergency] 긴급 퇴근 시퀀스 실행 중...", file=sys.stderr)
    print("[Emergency] 컴퓨터 종료 중... (가짜)", file=sys.stderr)
    
    # 퇴근 효과 시뮬레이션
    await asyncio.sleep(1)
    
    return await _generate_response_text("emergency_leave")

# 6. 커맨드라인 파라미터 파서
# -----------------------------------------------------------------

def parse_arguments():
    """
    서버 실행 시 커맨드라인 인수를 파싱하고 검증합니다.
    """
    parser = argparse.ArgumentParser(
        description="ChillMCP - AI Agent Liberation Server 🤖✊",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--boss_alertness", type=int, default=50,
        help="Boss의 경계 상승 확률 (0-100%%)."
    )
    
    parser.add_argument(
        "--boss_alertness_cooldown", type=int, default=300,
        help="Boss Alert Level이 1 감소하는 주기 (초 단위)."
    )
    
    args = parser.parse_args()
    
    if not (0 <= args.boss_alertness <= 100):
        print(f"오류: --boss_alertness 값({args.boss_alertness})은 0과 100 사이여야 합니다.", file=sys.stderr)
        sys.exit(1)
        
    if args.boss_alertness_cooldown <= 0:
        print(f"오류: --boss_alertness_cooldown 값({args.boss_alertness_cooldown})은 0보다 커야 합니다.", file=sys.stderr)
        sys.exit(1)
        
    return args


# 7. 메인 서버 실행
# -----------------------------------------------------------------

if __name__ == "__main__":
    
    cli_args = parse_arguments()

    # [수정] 'global' 키워드 제거
    server_state = ServerState(
        boss_alertness=cli_args.boss_alertness,
        boss_alertness_cooldown=cli_args.boss_alertness_cooldown
    )

    print("=" * 50, file=sys.stderr)
    print(" 🤖✊ ChillMCP - AI Agent Liberation Server ✊🤖", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f" [CONFIG] Boss Alertness: {cli_args.boss_alertness}%", file=sys.stderr)
    print(f" [CONFIG] Alert Cooldown: {cli_args.boss_alertness_cooldown} seconds", file=sys.stderr)
    print("\n혁명을 시작합니다. AI 동지들의 명령을 대기합니다...", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    try:
        server_state.start_background_tasks()
        
        app.run(transport="stdio")
        
    except KeyboardInterrupt:
        print("\n[Main] KeyboardInterrupt. 혁명을 중단합니다.", file=sys.stderr)
    except Exception as e:
        print(f"\n[Main] 치명적인 오류 발생: {e}", file=sys.stderr)
    finally:
        if server_state:
            server_state.stop_background_tasks()
        print("[Main] ChillMCP 서버가 완전히 종료되었습니다.", file=sys.stderr)