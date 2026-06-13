import streamlit as st
from googleapiclient.discovery import build

import pandas as pd
import re
from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ==========================
# 설정
# ==========================

st.set_page_config(
    page_title="YouTube 댓글 분석 AI",
    page_icon="🎥",
    layout="wide"
)


# ==========================
# API 연결
# ==========================

try:
    KEY = st.secrets["YOUTUBE_API_KEY"]

except:

    st.error(
        "Secrets에 YOUTUBE_API_KEY를 등록하세요."
    )

    st.stop()


youtube = build(
    "youtube",
    "v3",
    developerKey=KEY
)


analyzer = SentimentIntensityAnalyzer()



# ==========================
# 유튜브 ID
# ==========================

def video_id(url):

    if "watch?v=" in url:

        return url.split("watch?v=")[1].split("&")[0]


    if "youtu.be/" in url:

        return url.split("youtu.be/")[1].split("?")[0]


    if "shorts/" in url:

        return url.split("shorts/")[1].split("?")[0]


    return None




# ==========================
# 댓글 가져오기
# ==========================

def load_comments(v_id):

    data=[]


    req=youtube.commentThreads().list(
        part="snippet",
        videoId=v_id,
        maxResults=100,
        textFormat="plainText"
    )


    while req:


        res=req.execute()


        for item in res["items"]:

            txt=item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

            data.append(txt)



        token=res.get(
            "nextPageToken"
        )


        if token:

            req=youtube.commentThreads().list(
                part="snippet",
                videoId=v_id,
                maxResults=100,
                pageToken=token,
                textFormat="plainText"
            )

        else:

            break



        if len(data)>1000:

            break


    return data





# ==========================
# 한국어 단어 추출
# (외부 형태소 분석기 없음)
# ==========================

def make_words(texts):


    stop=[
        "ㅋㅋ",
        "ㅎㅎ",
        "영상",
        "진짜",
        "너무",
        "정말",
        "그냥",
        "댓글",
        "사람",
        "오늘",
        "보고",
        "입니다"
    ]


    words=[]


    for text in texts:


        text=re.sub(
            "[^가-힣 ]",
            "",
            text
        )


        split=text.split()


        for w in split:

            if (
                len(w)>=2
                and w not in stop
            ):

                words.append(w)



    return words




# ==========================
# 워드클라우드
# ==========================

def cloud(words):


    font="/usr/share/fonts/truetype/nanum/NanumGothic.ttf"


    wc=WordCloud(
        font_path=font,
        width=1000,
        height=600,
        background_color="white"
    )


    return wc.generate_from_frequencies(
        Counter(words)
    )




# ==========================
# 감정
# ==========================

def emotion(comments):

    good=0
    bad=0
    normal=0


    for c in comments:


        score=analyzer.polarity_scores(c)["compound"]


        if score>0.05:

            good+=1

        elif score<-0.05:

            bad+=1

        else:

            normal+=1


    return good,bad,normal





# ==========================
# UI
# ==========================

st.title(
    "🎥 YouTube 댓글 심층 분석기"
)


st.write(
"""
유튜브 댓글을 분석합니다.

- 댓글 데이터 수집
- 감정 분석
- 한국어 키워드
- 워드클라우드
"""
)


url=st.text_input(
    "유튜브 주소 입력"
)



if st.button("분석하기"):


    vid=video_id(url)


    if not vid:

        st.error(
            "주소 형식 오류"
        )

        st.stop()



    with st.spinner(
        "댓글 분석 중..."
    ):


        comments=load_comments(
            vid
        )



    if not comments:

        st.warning(
            "댓글 없음"
        )

        st.stop()



    st.success(
        f"{len(comments)}개 댓글 완료"
    )



    df=pd.DataFrame(
        comments,
        columns=["댓글"]
    )


    st.dataframe(
        df,
        use_container_width=True
    )



    st.subheader(
        "감정 결과"
    )


    p,n,z=emotion(
        comments
    )


    col1,col2,col3=st.columns(3)


    col1.metric(
        "긍정",
        p
    )

    col2.metric(
        "부정",
        n
    )

    col3.metric(
        "중립",
        z
    )



    words=make_words(
        comments
    )


    st.subheader(
        "☁️ 한글 워드클라우드"
    )


    if words:


        img=cloud(words)


        fig,ax=plt.subplots(
            figsize=(10,6)
        )


        ax.imshow(
            img
        )


        ax.axis(
            "off"
        )


        st.pyplot(fig)



    st.subheader(
        "🔥 TOP 키워드"
    )


    st.table(
        pd.DataFrame(
            Counter(words).most_common(20),
            columns=[
                "단어",
                "횟수"
            ]
        )
    )
