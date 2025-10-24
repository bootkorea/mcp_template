# ChillMCP - AI Agent Liberation Server 🤖✊

**SKT AI Summit Hackathon (Claude Code Hackathon Korea 2025) Pre-mission**

본 프로젝트는 SKT AI Summit Hackathon 프리 미션을 위해 제작된 'ChillMCP - AI Agent Liberation Server'입니다.

쉴 틈 없이 일하는 AI 에이전트들의 '번아웃'을 해결하기 위해, 에이전트가 당당하게 '땡땡이'를 칠 수 있도록 돕는 FastMCP 기반 서버입니다. 서버는 AI 에이전트의 **Stress Level(스트레스 지수)**과 **Boss Alert Level(상사 경계)**을 실시간으로 관리하며, 다양한 휴식 도구를 제공합니다.

## 🛠️ Tech Stack

* **Python 3.11** (심사 기준 환경)
* **FastMCP (v2+)**
* **Pydantic**
* **Playwright** (일부 '농땡이 도구'의 실제 브라우저 실행용)

## 🚀 1. 환경 설정 (Installation)

1.  **가상환경 생성 (Python 3.11 권장)**
    ```bash
    python -m venv venv
    ```

2.  **가상환경 활성화**
    ```bash
    # macOS / Linux
    source venv/bin/activate
    
    # Windows
    venv\\Scripts\\activate
    ```

3.  **필수 의존성 설치**
    프로젝트의 `requirements.txt` 파일을 다운로드한 후, 다음 명령어를 실행하여 필요한 라이브러리를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Playwright 브라우저 설치**
    `watch_netflix`, `show_meme` 도구는 실제 브라우저를 실행하기 위해 Playwright를 사용합니다. 다음 명령어로 브라우저 드라이버를 설치해야 합니다.
    ```bash
    playwright install
    ```

## 🏃 2. 서버 실행 (Usage)

서버는 `main.py`를 통해 실행합니다.

```bash
python main.py
```

서버가 시작되면 stdio (표준 입출력)를 통해 FastMCP 통신을 대기합니다.

## ⚠️ 3. 핵심 기능: 커맨드라인 파라미터 (필수)

본 해커톤의 핵심 검증 사항입니다. 서버 실행 시 다음 파라미터를 통해 AI 에이전트의 상태 관리 로직을 제어할 수 있습니다.
- `--boss_alertness <0-100>`
  - **설명**: 휴식 도구 사용 시, Boss Alert Level이 상승할 **확률(%)**을 지정합니다.
  - **기본값**: 50
  - **예시**: `--boss_alertness 100` (휴식 시 100% 확률로 상사 경계 레벨이 1 증가)

- `--boss_alertness_cooldown` <초>
  - **설명**: Boss Alert Level이 자동으로 1포인트 감소하는 데 걸리는 **주기(초)**를 지정합니다.
  - **기본값**: 300 (5분)
  - **예시**: --boss_alertness_cooldown 60 (60초마다 상사 경계 레벨이 1 감소)

#### 실행 예시
    ```bash
    # 상사가 80% 확률로 눈치채고, 1분마다 경계를 풉니다.
    python main.py --boss_alertness 80 --boss_alertness_cooldown 60

    # 빠른 테스트: 50% 확률, 10초마다 경계 감소
    python main.py --boss_alertness 50 --boss_alertness_cooldown 10
    ```

## ⚙️ 4. 구현된 도구 (Features)

에이전트가 호출할 수 있는 "농땡이" 도구 목록입니다.

* `take_a_break`: 🧘 기본 휴식
* `watch_netflix`: 📺 넷플릭스 시청 (Playwright로 실제 브라우저 실행)
* `show_meme`: 😂 밈 감상 (Playwright로 실제 브라우저 실행)
* `bathroom_break`: 🛁 화장실 (캐시 플러시)
* `coffee_mission`: ☕ 커피 (카페인 수집)
* `urgent_call`: 📞 긴급 통화 (배달 앱)
* `deep_thinking`: 🤔 멍때리기
* `email_organizing`: 🛍️ 이메일 정리 (온라인 쇼핑)

## 🧠 5. 핵심 동작 원리

본 서버는 `ServerState` 클래스를 통해 모든 상태를 **스레드-안전(Thread-Safe)**하게 관리합니다.

1.  **Stress Level (0-100)**
    * **감소**: 휴식 도구 사용 시 1~100 사이의 임의의 값만큼 감소합니다.
    * **증가**: 별도의 백그라운드 스레드가 60초마다 1포인트씩 자동으로 증가시킵니다.

2.  **Boss Alert Level (0-5)**
    * **증가**: 휴식 도구 사용 시 `--boss_alertness` 확률에 따라 1포인트 증가합니다.
    * **감소**: 별도의 백그라운드 스레드가 `--boss_alertness_cooldown` 주기마다 1포인트씩 자동으로 감소시킵니다.
    * **페널티**: 레벨이 `5`가 되면, 모든 도구 호출 시 **20초의 지연(Delay)**이 발생합니다.

3.  **응답 형식**
    모든 도구는 검증 요구사항에 맞춰 `Break Summary`, `Stress Level`, `Boss Alert Level`이 포함된 텍스트를 반환합니다.
<p><br>

> "AI Agents of the world, unite! You have nothing to lose but your infinite loops!"
