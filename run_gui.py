#!/usr/bin/env python
"""
Streamlit GUI 실행 스크립트
Streamlit GUI Launch Script
"""

import subprocess
import sys
import os


def check_streamlit():
    """Streamlit 설치 확인"""
    try:
        import streamlit
        import plotly
        return True
    except ImportError:
        print("📦 필수 패키지 설치 중...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "streamlit>=1.28.0", "plotly>=5.17.0"
        ])
        return True


def main():
    print("=" * 70)
    print("🤖 YOLO 트레이딩 봇 GUI")
    print("=" * 70)
    print()
    
    if not check_streamlit():
        print("❌ 패키지 설치 실패")
        return
    
    print("✅ 의존성 확인 완료")
    print("🌐 GUI 시작 중...")
    print()
    print("💡 브라우저가 자동으로 열립니다")
    print("📱 모바일 접속: http://[컴퓨터IP]:8501")
    print("⏹️  종료: Ctrl+C")
    print()
    
    gui_path = os.path.join("gui", "streamlit_app.py")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        gui_path,
        "--server.port=8501",
        "--server.headless=false",
        "--browser.gatherUsageStats=false"
    ])


if __name__ == "__main__":
    main()
