import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Population Trends 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **인구 추이 데이터셋**  
                - 파일명: `population_trends.csv`  
                - 설명: 한국 각 지역의 연도별 인구·출생아수·사망자수 데이터  
                - 주요 변수:  
                  - `연도`: 연도  
                  - `지역`: 행정구역명  
                  - `인구`: 해당 연도의 인구수  
                  - `출생아수(명)`: 해당 연도의 출생아수  
                  - `사망자수(명)`: 해당 연도의 사망자수  
                """)
# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        import io
        st.title("📊 Population Trends EDA")

        # 1) CSV 업로드
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv")
            return

        # 2) 기본 전처리
        df = pd.read_csv(uploaded)
        # 세종 결측치 처리 및 숫자형 변환
        mask_sejong = df['지역'] == '세종'
        df.loc[mask_sejong, ['인구','출생아수(명)','사망자수(명)']] = \
            df.loc[mask_sejong, ['인구','출생아수(명)','사망자수(명)']].replace('-', 0)
        for col in ['인구','출생아수(명)','사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 2-1) 한글 공백 제거 & 영어명 매핑
        df['지역'] = df['지역'].astype(str).str.strip()
        region_map = {
            '전국':   'Nationwide',
            '서울':   'Seoul',
            '부산':   'Busan',
            '대구':   'Daegu',
            '인천':   'Incheon',
            '광주':   'Gwangju',
            '대전':   'Daejeon',
            '울산':   'Ulsan',
            '세종':   'Sejong',
            '경기도': 'Gyeonggi',
            '경기':   'Gyeonggi',
            '강원':   'Gangwon',
            '충북':   'Chungbuk',
            '충남':   'Chungnam',
            '전북':   'Jeonbuk',
            '전남':   'Jeonnam',
            '경북':   'Gyeongbuk',
            '경남':   'Gyeongnam',
            '제주':   'Jeju'
        }
        df['region_eng'] = df['지역'].map(region_map)

        # 3) 탭 구성
        tabs = st.tabs([
            "기초 통계",
            "연도별 추이",
            "지역별 분석",
            "변화량 분석",
            "시각화"
        ])

        # ── 탭1: 기초 통계
        with tabs[0]:
            st.header("📝 Basic Data Overview")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())

            st.subheader("Descriptive Statistics")
            st.dataframe(df.describe())

            st.subheader("Missing & Duplicates")
            st.write(df.isnull().sum())
            st.write(f"- Duplicates: {df.duplicated().sum()} rows")

        # ── 탭2: 연도별 전체 인구 추이 + 2035 예측
        with tabs[1]:
            st.header("📈 Yearly Population Trend")
            df_nat = df[df['region_eng'] == "Nationwide"].sort_values('연도')

            # 실제 데이터
            fig, ax = plt.subplots()
            ax.plot(df_nat['연도'], df_nat['인구'], marker='o', label='Actual')

            # 최근 3년 net change 평균으로 2035 예측
            last3 = df_nat.tail(3).copy()
            last3['net'] = last3['출생아수(명)'] - last3['사망자수(명)']
            avg_net = last3['net'].mean()

            ly = int(df_nat['연도'].max())
            lp = float(df_nat.loc[df_nat['연도'] == ly, '인구'])
            years_pred = list(range(ly + 1, 2036))
            pop_pred = [lp + avg_net * (y - ly) for y in years_pred]

            ax.plot(years_pred, pop_pred,
                    linestyle='--', marker='x', label='Projected to 2035')
            ax.set_title("Yearly Population & Projection")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

            st.write(f"**Projected population in 2035:** {pop_pred[-1]:,.0f}")

        # ── 탭3: 지역별 분석 (5년 변화량 & 변화율)
        with tabs[2]:
            st.header("📊 Regional 5-Year Change Ranking")
            years = sorted(df['연도'].unique())
            last, prev = years[-1], years[-1] - 5

            sub = df[df['연도'].isin([prev, last])]
            piv = (sub
                   .pivot(index='region_eng', columns='연도', values='인구')
                   .drop('Nationwide', errors='ignore'))
            piv['change'] = piv[last] - piv[prev]
            piv['pct_change'] = piv['change'] / piv[prev] * 100

            fig, ax = plt.subplots()
            sns.barplot(x=piv['change'] / 1_000, y=piv.index, ax=ax)
            ax.set_title("5-Year Population Change")
            ax.set_xlabel("Change (thousands)")
            for i, v in enumerate(piv['change'] / 1_000):
                ax.text(v, i, f"{v:,.1f}", va='center')
            st.pyplot(fig)

            fig, ax = plt.subplots()
            sns.barplot(x=piv['pct_change'], y=piv.index, ax=ax)
            ax.set_title("5-Year Population % Change")
            ax.set_xlabel("Percentage Change")
            for i, v in enumerate(piv['pct_change']):
                ax.text(v, i, f"{v:.1f}%", va='center')
            st.pyplot(fig)

        # ── 탭4: 증감률 상위 100개 사례
        with tabs[3]:
            st.header("🔍 Top 100 Yearly Population Diffs")
            df_diff = df.copy()
            df_diff['diff'] = df_diff.groupby('region_eng')['인구'].diff()
            df_diff = df_diff[df_diff['region_eng'] != "Nationwide"]

            top100 = (df_diff.nlargest(100, 'diff')
                      .loc[:, ['region_eng','연도','diff']]
                      .rename(columns={'region_eng':'Region','연도':'Year','diff':'Diff'})
                      .reset_index(drop=True))
            styled = (top100.style
                      .background_gradient(subset=['Diff'], cmap='bwr_r')
                      .format({'Diff':'{:,.0f}'}))
            st.dataframe(styled)

        # ── 탭5: 누적 영역 그래프
        with tabs[4]:
            st.header("🌐 Stacked Area Plot")
            df_area = df[df['region_eng'] != "Nationwide"]
            piv_area = df_area.pivot(index='연도', columns='region_eng', values='인구')

            fig, ax = plt.subplots()
            piv_area.plot.area(ax=ax, colormap='tab20', alpha=0.8)
            ax.set_title("Population by Region Over Years")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()