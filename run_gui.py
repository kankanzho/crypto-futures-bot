"""
YOLO 트레이딩 봇 GUI 실행 스크립트
Streamlit 기반 웹 인터페이스를 시작합니다
"""

import subprocess
import sys
import os

def main():
    """
    Streamlit GUI 실행
    Run Streamlit GUI
    """
    print("=" * 60)
    print("🤖 YOLO 트레이딩 봇 GUI 시작")
    print("🚀 YOLO Trading Bot GUI Starting")
    print("=" * 60)
    print()
    print("📱 브라우저가 자동으로 열립니다...")
    print("📱 Browser will open automatically...")
    print()
    print("🌐 URL: http://localhost:8501")
    print()
    print("💡 종료하려면 Ctrl+C를 누르세요")
    print("💡 Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Streamlit 설치 확인
    try:
        import streamlit
    except ImportError:
        print("❌ 오류: Streamlit이 설치되지 않았습니다.")
        print("❌ Error: Streamlit is not installed.")
        print()
        print("설치 방법: pip install streamlit plotly")
        print("Install: pip install streamlit plotly")
        return
    
    # GUI 디렉토리로 이동
    gui_path = os.path.join(os.path.dirname(__file__), "gui", "streamlit_app.py")
    
    # Streamlit 실행
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            gui_path,
            "--server.port=8501",
            "--server.address=localhost"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit 실행 중 오류 발생: {e}")
        print(f"❌ Error running Streamlit: {e}")
    except KeyboardInterrupt:
        print("\n\n종료됨")
        print("Stopped")

if __name__ == "__main__":
    main()
