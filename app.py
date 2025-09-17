import streamlit as st
from ultralytics import YOLO
import cv2
import tempfile
from PIL import Image
import numpy as np
import sqlite3
import hashlib
import os


# ================= DATABASE SETUP =================
def init_database():
    """Initialize database and create users table if not exists"""
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect("app.db")


def create_user(username, email, password):
    if not username or not email or not password:
        return False, "Vui lòng nhập đầy đủ thông tin!"

    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự!"

    conn = get_connection()
    c = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, password_hash))
        conn.commit()
        return True, "Đăng ký thành công!"
    except sqlite3.IntegrityError:
        return False, "Tên đăng nhập hoặc email đã tồn tại!"
    finally:
        conn.close()


def check_login(username, password):
    if not username or not password:
        return False

    conn = get_connection()
    c = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id FROM users WHERE username=? AND password_hash=?",
              (username, password_hash))
    result = c.fetchone()
    conn.close()
    return result is not None


# ================= APP CONFIG =================
st.set_page_config(
    page_title="YOLO AI Vision",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_database()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "username" not in st.session_state:
    st.session_state.username = ""

# ================= MODERN CSS STYLING =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Hide Streamlit elements */
header[data-testid="stHeader"] {visibility: hidden;}
.stDeployButton {display: none;}
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* Main app styling */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: 'Inter', sans-serif;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
    background-size: 400% 400%;
    animation: gradientShift 8s ease infinite;
    padding: 2.5rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.main-title {
    font-size: 3.5rem;
    font-weight: 800;
    color: white;
    text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
    margin: 0;
    letter-spacing: -1px;
}

.main-subtitle {
    font-size: 1.3rem;
    color: rgba(255,255,255,0.95);
    margin-top: 0.8rem;
    font-weight: 400;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

/* Navigation */
.nav-container {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-bottom: 2.5rem;
    flex-wrap: wrap;
    padding: 0 1rem;
}

.stButton > button {
    background: linear-gradient(145deg, #ffffff, #f8fafc) !important;
    border: 2px solid rgba(79, 70, 229, 0.1) !important;
    padding: 1rem 2rem !important;
    border-radius: 15px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: #1f2937 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important;
    height: auto !important;
    min-height: 3rem !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 30px rgba(0,0,0,0.2) !important;
    background: linear-gradient(145deg, #f8fafc, #ffffff) !important;
    border-color: rgba(79, 70, 229, 0.3) !important;
}

.stButton > button:active {
    transform: translateY(-1px) !important;
}

/* Content cards */
.content-card {
    background: rgba(255, 255, 255, 0.95);
    padding: 2.5rem;
    border-radius: 25px;
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,0.3);
    margin-bottom: 2rem;
}

/* Form styling */
.login-form {
    max-width: 450px;
    margin: 0 auto;
    padding: 2.5rem;
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    border-radius: 25px;
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    border: 1px solid rgba(0,0,0,0.05);
}

.form-title {
    text-align: center;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 2rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Input styling */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 2px solid #e5e7eb !important;
    padding: 0.8rem 1rem !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    background: #ffffff !important;
}

.stTextInput > div > div > input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}

/* Primary buttons */
.primary-button button {
    background: linear-gradient(145deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 16px rgba(79, 70, 229, 0.3) !important;
}

.primary-button button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 24px rgba(79, 70, 229, 0.4) !important;
    background: linear-gradient(145deg, #7c3aed, #4f46e5) !important;
}

/* Success/Error messages */
.success-message {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    text-align: center;
    font-weight: 500;
    margin: 1rem 0;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.error-message {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    text-align: center;
    font-weight: 500;
    margin: 1rem 0;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* Demo section */
.demo-header {
    text-align: center;
    margin-bottom: 2rem;
}

.demo-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.user-info {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 500;
    box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
}

/* Radio buttons */
.stRadio > div {
    display: flex;
    justify-content: center;
    gap: 2rem;
    background: rgba(255,255,255,0.1);
    padding: 1rem;
    border-radius: 15px;
    margin-bottom: 2rem;
}

/* File uploader */
.uploadedFile {
    background: linear-gradient(145deg, #f9fafb, #ffffff) !important;
    border-radius: 15px !important;
    padding: 2rem !important;
    border: 2px dashed #d1d5db !important;
    text-align: center !important;
}

/* Contact info */
.contact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.contact-card {
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 15px 30px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    border: 1px solid rgba(0,0,0,0.05);
}

.contact-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}

.contact-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Feature cards */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    margin: 3rem 0;
}

.feature-card {
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    padding: 2.5rem;
    border-radius: 20px;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 15px 30px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.03);
}

.feature-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
}

.feature-icon {
    font-size: 3.5rem;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.feature-title {
    font-size: 1.6rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 1rem;
}

.feature-desc {
    color: #6b7280;
    line-height: 1.6;
    font-size: 1rem;
}

/* Footer */
.footer {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(15px);
    padding: 2.5rem;
    text-align: center;
    border-radius: 25px;
    margin-top: 4rem;
    border: 1px solid rgba(255,255,255,0.2);
}

.footer-text {
    color: white;
    font-weight: 500;
    font-size: 1.1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

/* Responsive */
@media (max-width: 768px) {
    .main-title { font-size: 2.5rem; }
    .main-subtitle { font-size: 1.1rem; }
    .nav-container { gap: 1rem; }
    .content-card { padding: 1.5rem; }
    .login-form { padding: 2rem; margin: 0 1rem; }
}

/* Logout button */
.logout-button button {
    background: linear-gradient(145deg, #ef4444, #dc2626) !important;
    color: white !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

.logout-button button:hover {
    background: linear-gradient(145deg, #dc2626, #b91c1c) !important;
    transform: translateY(-1px) !important;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
    <div class="main-header">
        <div class="main-title">🎯 HAUI_SuperModel</div>
        <div class="main-subtitle">Phát triển bởi nhóm HAUI_SuperModel</div>
    </div>
""", unsafe_allow_html=True)


# ================= NAVIGATION =================
def render_navigation():
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)

    if st.session_state.page == "home":
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📞 Liên hệ", key="contact_btn"):
                st.session_state.page = "contact"

        with col2:
            if st.button("🔐 Đăng nhập", key="login_btn"):
                st.session_state.page = "login"

        with col3:
            if st.button("📝 Đăng ký", key="signup_btn"):
                st.session_state.page = "signup"

        with col4:
            if st.session_state.logged_in:
                if st.button("🚀 AI Demo", key="demo_btn"):
                    st.session_state.page = "demo"
            else:
                if st.button("🎮 Dùng thử Demo", key="trial_btn"):
                    st.info("Vui lòng đăng nhập để sử dụng AI Demo!")

    else:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("🏠 Trang chủ", key="home_btn"):
                st.session_state.page = "home"

        with col2:
            if st.button("📞 Liên hệ", key="contact_btn"):
                st.session_state.page = "contact"

        with col3:
            if st.button("🔐 Đăng nhập", key="login_btn"):
                st.session_state.page = "login"

        with col4:
            if st.button("📝 Đăng ký", key="signup_btn"):
                st.session_state.page = "signup"

        with col5:
            if st.session_state.logged_in:
                st.markdown('<div class="logout-button">', unsafe_allow_html=True)
                if st.button("🚪 Đăng xuất", key="logout_btn"):
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.page = "home"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                if st.button("🚀 AI Demo", key="demo_btn"):
                    st.warning("Vui lòng đăng nhập để sử dụng AI Demo!")

    st.markdown('</div>', unsafe_allow_html=True)


render_navigation()


# ================= LOAD MODEL =================
@st.cache_resource
def load_model():
    try:
        return YOLO("best.pt")
    except Exception as e:
        st.error(f"❌ Không thể tải model YOLO: {str(e)}")
        return None


model = load_model()

# ================= PAGES =================
if st.session_state.page == "home":
    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    st.markdown("# 🚀 Chào mừng đến với YOLO AI Vision")
    st.markdown("### Nền tảng nhận diện đối tượng thông minh sử dụng công nghệ AI tiên tiến")

    if st.session_state.logged_in:
        st.markdown(
            f'<div class="user-info">👋 Xin chào <strong>{st.session_state.username}</strong>! Chào mừng bạn quay lại.</div>',
            unsafe_allow_html=True)

    # Feature showcase
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)

    features = [
        {
            "icon": "🎯",
            "title": "Nhận diện chính xác",
            "desc": "Công nghệ YOLO v8 với độ chính xác cao, nhận diện real-time các đối tượng trong ảnh và video"
        },
        {
            "icon": "⚡",
            "title": "Tốc độ nhanh",
            "desc": "Xử lý hình ảnh và video với tốc độ lightning-fast, phản hồi tức thời"
        },
        {
            "icon": "📱",
            "title": "Đa nền tảng",
            "desc": "Hỗ trợ upload ảnh, video và webcam trên mọi thiết bị với giao diện responsive"
        },
        {
            "icon": "🔒",
            "title": "Bảo mật cao",
            "desc": "Hệ thống đăng nhập an toàn với mã hóa SHA-256 và quản lý phiên bảo mật"
        }
    ]

    for i in range(0, len(features), 2):
        col1, col2 = st.columns(2)

        with col1:
            if i < len(features):
                feature = features[i]
                st.markdown(f"""
                    <div class="feature-card">
                        <div class="feature-icon">{feature['icon']}</div>
                        <div class="feature-title">{feature['title']}</div>
                        <div class="feature-desc">{feature['desc']}</div>
                    </div>
                """, unsafe_allow_html=True)

        with col2:
            if i + 1 < len(features):
                feature = features[i + 1]
                st.markdown(f"""
                    <div class="feature-card">
                        <div class="feature-icon">{feature['icon']}</div>
                        <div class="feature-title">{feature['title']}</div>
                        <div class="feature-desc">{feature['desc']}</div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.info("💡 **Hướng dẫn:** Đăng ký tài khoản hoặc đăng nhập để trải nghiệm đầy đủ tính năng AI Demo!")
    else:
        st.success("✨ **Sẵn sàng sử dụng:** Nhấn vào nút 'AI Demo' để bắt đầu nhận diện đối tượng!")

    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "contact":
    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    st.markdown("# 📞 Thông tin liên hệ")
    st.markdown("### Chúng tôi luôn sẵn sàng hỗ trợ và kết nối với bạn!")

    st.markdown('<div class="contact-grid">', unsafe_allow_html=True)

    contacts = [
        {"icon": "📧", "title": "Email Support", "info": "team@hackathon.ai", "desc": "Hỗ trợ kỹ thuật 24/7"},
        {"icon": "💬", "title": "Live Chat", "info": "Messenger", "desc": "Phản hồi trong 5 phút"},
        {"icon": "📱", "title": "Hotline", "info": "+84 123 456 789", "desc": "Tư vấn trực tiếp"},
        {"icon": "🌐", "title": "Website", "info": "yolovision.ai", "desc": "Tài liệu và hướng dẫn"}
    ]

    for contact in contacts:
        st.markdown(f"""
            <div class="contact-card">
                <div class="contact-icon">{contact['icon']}</div>
                <h3>{contact['title']}</h3>
                <p style="font-weight: 600; color: #4f46e5; font-size: 1.1rem;">{contact['info']}</p>
                <p style="color: #6b7280;">{contact['desc']}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 Gửi tin nhắn cho chúng tôi")

    with st.form("contact_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("👤 Họ và tên")
            email = st.text_input("📧 Email")

        with col2:
            phone = st.text_input("📱 Số điện thoại")
            subject = st.selectbox("📋 Chủ đề", ["Hỗ trợ kỹ thuật", "Góp ý", "Hợp tác", "Khác"])

        message = st.text_area("💬 Tin nhắn", height=100)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="primary-button">', unsafe_allow_html=True)
            if st.form_submit_button("📤 Gửi tin nhắn", use_container_width=True):
                if name and email and message:
                    st.markdown('<div class="success-message">✅ Cảm ơn bạn! Tin nhắn đã được gửi thành công.</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">❌ Vui lòng nhập đầy đủ thông tin bắt buộc.</div>',
                                unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "signup":
    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    st.markdown('<div class="login-form">', unsafe_allow_html=True)

    st.markdown('<div class="form-title">📝 Đăng ký tài khoản</div>', unsafe_allow_html=True)

    with st.form("signup_form"):
        new_user = st.text_input("👤 Tên đăng nhập", placeholder="Nhập tên đăng nhập của bạn")
        new_email = st.text_input("📧 Email", placeholder="Nhập địa chỉ email")
        new_pw = st.text_input("🔒 Mật khẩu", type="password", placeholder="Tạo mật khẩu (ít nhất 6 ký tự)")
        confirm_pw = st.text_input("🔒 Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")

        agree_terms = st.checkbox("Tôi đồng ý với điều khoản sử dụng và chính sách bảo mật")

        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
        submit = st.form_submit_button("✨ Tạo tài khoản", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if submit:
            if not agree_terms:
                st.markdown('<div class="error-message">❌ Vui lòng đồng ý với điều khoản sử dụng!</div>',
                            unsafe_allow_html=True)
            elif new_pw != confirm_pw:
                st.markdown('<div class="error-message">❌ Mật khẩu xác nhận không khớp!</div>', unsafe_allow_html=True)
            else:
                ok, msg = create_user(new_user, new_email, new_pw)
                if ok:
                    st.markdown('<div class="success-message">🎉 ' + msg + ' Hãy đăng nhập để sử dụng!</div>',
                                unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown(f'<div class="error-message">❌ {msg}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Đã có tài khoản?** Nhấn 'Đăng nhập' ở menu trên để vào hệ thống.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "login":
    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    st.markdown('<div class="login-form">', unsafe_allow_html=True)

    st.markdown('<div class="form-title">🔐 Đăng nhập hệ thống</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("👤 Tên đăng nhập", placeholder="Nhập tên đăng nhập")
        password = st.text_input("🔒 Mật khẩu", type="password", placeholder="Nhập mật khẩu")

        remember_me = st.checkbox("Ghi nhớ đăng nhập")

        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 Đăng nhập", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if submit:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "demo"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "demo":
    if not st.session_state.logged_in:
        st.warning("⚠️ Vui lòng đăng nhập để sử dụng AI Demo.")
        st.stop()

    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    st.markdown('<div class="demo-header">', unsafe_allow_html=True)
    st.markdown('<div class="demo-title">🤖 YOLO AI Demo</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="user-info">Xin chào **{st.session_state.username}** 👋. Bắt đầu trải nghiệm YOLO AI!</div>',
        unsafe_allow_html=True)

    option = st.radio("Chọn chế độ:", ["📤 Upload Ảnh/Video", "📸 Webcam"], horizontal=True)

    if option == "📤 Upload Ảnh/Video":
        uploaded_file = st.file_uploader("Chọn ảnh hoặc video", type=["jpg", "jpeg", "png", "mp4", "avi"])
        if uploaded_file is not None:
            if uploaded_file.type.startswith("image"):
                image = Image.open(uploaded_file).convert("RGB")
                results = model(image)
                st.image(results[0].plot(), caption="Kết quả YOLO", use_column_width=True)
            elif uploaded_file.type.startswith("video"):
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_file.read())
                cap = cv2.VideoCapture(tfile.name)
                stframe = st.empty()
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    results = model(frame)
                    annotated = results[0].plot()
                    stframe.image(annotated, channels="BGR", use_column_width=True)
                cap.release()

    elif option == "📸 Webcam":
        st.write("🎥 Bật webcam realtime")
        run = st.checkbox("▶️ Start Webcam")
        FRAME_WINDOW = st.image([])
        cap = cv2.VideoCapture(0)
        while run:
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Không mở được camera")
                break
            results = model(frame)
            annotated = results[0].plot()
            FRAME_WINDOW.image(annotated, channels="BGR", use_column_width=True)
        cap.release()

    st.markdown('</div>', unsafe_allow_html=True)

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    <div class="footer-text">© 2025 YOLO AI Vision | Developed by HAUI_SuperModel</div>
</div>
""", unsafe_allow_html=True)
