
# ![header image](data/headerImage.jpg)

import asyncio
import streamlit as st
import random
import time
import json
from gtts import gTTS
from io import BytesIO
import base64

from utils.init import initialize
from utils.counter import initialize_user_count, increment_user_count, decrement_user_count, get_user_count
from utils.word_generator import WordGenerator
from utils.TelegramSender import TelegramSender

# צבעים מותאמים לילדים
COLORS = {
    "background": "#FFFFFF",  # לבן
    "title": "#FF69B4",       # ורוד חזק
    "text": "#4B0082",        # אינדיגו
    "button": "#00CED1",      # טורקיז
    "correct": "#32CD32",     # ירוק בהיר
    "incorrect": "#FF6347",   # אדום-כתום
}

DIFFICULTY_LEVELS = {
    "easy": {"name": "קל", "time": 20, "color": COLORS["correct"]},
    "medium": {"name": "בינוני", "time": 15, "color": COLORS["button"]},
    "hard": {"name": "קשה", "time": 10, "color": COLORS["incorrect"]},
}

def start_over():
    for key in list(st.session_state.keys()):
        if key not in ['counted', 'user_count', 'age', 'num_words']:
            del st.session_state[key]

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()

def generate_pastel_color():
    # Generate a random pastel color
    r = random.randint(180, 255)
    g = random.randint(180, 255)
    b = random.randint(180, 255)
    return f'rgb({r}, {g}, {b})'

def start_over():
    for key in list(st.session_state.keys()):
        if key not in ['counted', 'user_count', 'age', 'num_words', 'used_words']:
            del st.session_state[key]
    st.session_state.used_words = []

# Initialize TelegramSender
if 'telegram_sender' not in st.session_state:
    st.session_state.telegram_sender = TelegramSender()

# Increment user count if this is a new session
if 'counted' not in st.session_state:
    st.session_state.counted = True
    increment_user_count()

# Initialize user count
initialize_user_count()

def play_sound(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            <script>
            var audio = document.getElementsByTagName("audio")[0];
            audio.play();
            </script>
            """
        st.markdown(md, unsafe_allow_html=True)
    
def main():
    header_content, image_path, footer_content = initialize()    

    # Load sound effects
    correct_sound = "sounds/correct.mp3"
    incorrect_sound = "sounds/incorrect.mp3"

    # Initialize session state variables
    if 'age' not in st.session_state:
        st.session_state.age = 7  # Default age
    if 'num_words' not in st.session_state:
        st.session_state.num_words = 5  # Default number of words
    if 'game_state' not in st.session_state:
        st.session_state.game_state = 'start'
    if 'words' not in st.session_state:
        st.session_state.words = []
    if 'current_word' not in st.session_state:
        st.session_state.current_word = None
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'failures' not in st.session_state:
        st.session_state.failures = 0
    if 'total_questions' not in st.session_state:
        st.session_state.total_questions = 0
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'selected_difficulty' not in st.session_state:
        st.session_state.selected_difficulty = None
    if 'timer_active' not in st.session_state:
        st.session_state.timer_active = True
    if 'waiting_for_next' not in st.session_state:
        st.session_state.waiting_for_next = False
    if 'used_words' not in st.session_state:
        st.session_state.used_words = []

    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COLORS['background']};
        }}
        .stButton>button {{
            background-color: {COLORS['button']};
            color: white;
        }}
        .stProgress > div > div {{
            background-color: {COLORS['button']};
        }}
    </style>
    """, unsafe_allow_html=True)

    # st.title("LinguaKid", anchor=False)
    st.markdown(f"<h2 style='text-align: center; color: {COLORS['title']};'>{header_content}</h2>", unsafe_allow_html=True)
    
    if image_path:
        st.image(image_path, use_column_width=True)

    if st.session_state.game_state in ['start', 'word_preview']:
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.age = st.number_input("הכנס את גילך:", min_value=3, max_value=100, value=st.session_state.age, step=1, key="age_input")

        with col2:
            st.session_state.num_words = st.number_input("מספר מילים למשחק:", min_value=5, max_value=20, value=st.session_state.num_words, step=1, key="word_count_input")

    if st.session_state.game_state in ['start', 'word_preview']:
        if st.button("יצירת מילים", use_container_width=True):
            word_generator = WordGenerator()
            retry_count = 0
            max_retries = 3
            with st.spinner('נא להמתין מייצר מילים...'):
                while retry_count < max_retries:
                    try:
                        st.session_state.words = word_generator.generate_words(
                            st.session_state.age, 
                            "medium", 
                            st.session_state.num_words, 
                            st.session_state.used_words
                        )
                        # Store only the English words
                        st.session_state.all_game_words = [word['english'] for word in st.session_state.words]
                        st.session_state.used_words.extend(st.session_state.all_game_words)
                        st.session_state.game_state = 'word_preview'
                        st.rerun()
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            error_message = f"שגיאה בטעינת המילים. מנסה שוב בעוד {4 - retry_count} שניות..."
                            with st.spinner(error_message):
                                time.sleep(3)
                        else:
                            st.error("לא הצלחנו לטעון מילים. אנא נסה שוב מאוחר יותר.")
                            break

        if st.session_state.game_state == 'word_preview' and st.session_state.words:
            st.markdown("### מילים לתרגול:")
            
            # Create a colorful table with the English words
            word_html = "<table style='width:100%; border-collapse: separate;'><tr>"
            colors = [generate_pastel_color() for _ in range(20)]  # Generate 20 unique pastel colors
            for i, word in enumerate(st.session_state.words):
                color = colors[i % len(colors)]                
                word_html += f"<td style='border: 2px solid #ddd; padding: 10px; text-align: center; background-color: {color};border-radius: 10px;font-size: 18px;font-weight: bold;box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>{word['english']}</td>"
                if (i + 1) % 4 == 0 and i != len(st.session_state.words) - 1:  # Start a new row every 4 words
                    word_html += "</tr><tr>"
            word_html += "</tr></table>"
            
            st.markdown(word_html, unsafe_allow_html=True)

            st.markdown(f"<h4 style='text-align: center; color: {COLORS['text']};'>בחרו את רמת הקושי כדי להתחיל:</h3>", unsafe_allow_html=True)          
            
            cols = st.columns(3)
            for i, (level, details) in enumerate(DIFFICULTY_LEVELS.items()):
                with cols[i]:
                    if st.button(f"{details['name']} - {details['time']} שניות", 
                                 key=level, 
                                 use_container_width=True,
                                 help=f"לחץ כאן כדי להתחיל במשחק ברמה {details['name']}"):
                        st.session_state.selected_difficulty = level
                        st.session_state.difficulty = level
                        st.session_state.game_state = 'play'
                        st.session_state.total_questions = len(st.session_state.words)
                        st.session_state.score = 0
                        st.session_state.failures = 0
                        st.session_state.current_word = None
                        st.session_state.start_time = time.time()
                        st.session_state.timer_active = True
                        st.session_state.waiting_for_next = False
                        st.rerun()

    elif st.session_state.game_state == 'play':
        game_container = st.container()
        with game_container:
            if st.button("התחל מחדש", use_container_width=True):
                start_over()
                st.rerun()

            if not st.session_state.current_word:
                if st.session_state.words:
                    st.session_state.current_word = st.session_state.words.pop(random.randint(0, len(st.session_state.words) - 1))
                    st.session_state.start_time = time.time()
                    st.session_state.timer_active = True
                    st.session_state.waiting_for_next = False
                else:
                    st.session_state.game_state = 'end'
                    st.rerun()            

            questions_left = len(st.session_state.words) + 1
            st.write(f"שאלה {st.session_state.total_questions - questions_left + 1} מתוך {st.session_state.total_questions}")

            current_time = time.time()
            if st.session_state.timer_active:
                time_left = max(0, DIFFICULTY_LEVELS[st.session_state.difficulty]["time"] - (current_time - st.session_state.start_time))
            else:
                time_left = 0
            progress = time_left / DIFFICULTY_LEVELS[st.session_state.difficulty]["time"]
            st.progress(progress)
            st.write(f"זמן נותר: {int(time_left)} שניות")

            st.markdown(f"""
            <div style='text-align: center;'>
                <span style='font-size: 72px; font-weight: bold; color: {COLORS['text']}; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);'>
                    {st.session_state.current_word['english']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            audio_file = text_to_speech(st.session_state.current_word['english'])
            st.audio(audio_file, format='audio/mp3')
            
            if time_left <= 0 and st.session_state.timer_active:
                st.error("הזמן נגמר!")
                st.session_state.failures += 1
                st.session_state.timer_active = False
                st.session_state.waiting_for_next = True
                st.rerun()

            cols = st.columns(2)
            for i, option in enumerate(st.session_state.current_word['options']):
                with cols[i % 2]:
                    button_color = COLORS['button']
                    if st.session_state.waiting_for_next and option == st.session_state.current_word['hebrew']:
                        button_color = COLORS['correct']
                    if st.button(option, key=f"option_{i}", use_container_width=True, 
                                 disabled=st.session_state.waiting_for_next and option != st.session_state.current_word['hebrew']):
                        if not st.session_state.waiting_for_next:
                            if option == st.session_state.current_word['hebrew']:
                                st.session_state.score += 1
                                st.success("נכון!")
                                play_sound(correct_sound)
                                time.sleep(2)
                                st.session_state.current_word = None
                                st.rerun()
                            else:
                                st.session_state.failures += 1
                                st.error(f"לא נכון. לחץ על התשובה הנכונה כדי להמשיך.")
                                play_sound(incorrect_sound)
                                time.sleep(1)
                                st.session_state.timer_active = False
                                st.session_state.waiting_for_next = True
                                st.rerun()
                        else:
                            st.session_state.current_word = None
                            st.session_state.waiting_for_next = False
                            st.rerun()

            st.markdown(
                f"""
                <div style='display: flex; justify-content: space-between;'>
                    <div style='color: {COLORS["correct"]};'>ניקוד: {st.session_state.score}</div>
                    <div style='color: {COLORS["incorrect"]};'>טעויות: {st.session_state.failures}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    elif st.session_state.game_state == 'end':
        end_game_container = st.container()
        with end_game_container:
            st.markdown(f"<h2 style='text-align: center; color: {COLORS['title']};'>המשחק הסתיים!</h2>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style='text-align: center; font-size: 24px;'>
                    <div style='color: {COLORS["correct"]};'>ניקוד סופי: {st.session_state.score}</div>
                    <div style='color: {COLORS["incorrect"]};'>טעויות: {st.session_state.failures}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Join the English words into a single string
            word_list = ", ".join(st.session_state.all_game_words)
            
            asyncio.run(send_telegram_message(
                f"Final score: {st.session_state.score}, "
                f"Mistakes: {st.session_state.failures}, "
                f"The words are: {word_list}"
            ))

            if st.button("שחק שוב", use_container_width=True):
                start_over()
                st.rerun()

    user_count = get_user_count(formatted=True)
    footer_with_count = f"{footer_content}\n\n<p class='user-count' style='color: {COLORS['text']};'>סה\"כ משתמשים: {user_count}</p>"
    st.markdown(footer_with_count, unsafe_allow_html=True)

    # Update the timer every second
    if st.session_state.game_state == 'play' and st.session_state.timer_active:
        time.sleep(1)
        st.rerun()


async def send_telegram_message(txt):
    sender = st.session_state.telegram_sender
    try:
        await sender.send_message(txt, "LinguKid")
    finally:
        await sender.close_session()

if __name__ == "__main__":
    main()