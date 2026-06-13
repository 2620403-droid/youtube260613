import streamlit as st
from googleapiclient.discovery import build

import pandas as pd
import re
import os
import requests

from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer



# =========================
# 설정
# =========================

st.set_page_config(
    page_title="YouTube 댓글 분석 AI",
    page_icon="🎬",
    layout="wide"
)



# =========================
# API KEY
# =========================

try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]

except:

    st.error(
        "Streamlit Secrets에 YOUTUBE_API_KEY를 추가해주세요."
    )

    st.stop()



youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)


sentiment = SentimentIntensityAnalyzer()



# =========================
# 한글 폰트 자동 설치
# =========================

def get_korean_font():

    font_file = "NanumGothic.ttf"


    if not os.path.exists(font_file):

        url = (
            "https://github.com/naver/nanumfont/"
            "raw/master/fonts/NanumGothic.ttf"
        )


        r = requests.get(url)


        with open(font_file, "wb") as f:

            f.write(r.content)



    return font_file





# =========================
# 영상 ID 추출
# =========================

def get_video_id(url):

    patterns = [

        r"v=([^&]+)",

        r"youtu\.be/([^?]+)",

        r"shorts/([^?]+)"

    ]


    for p in patterns:

        result = re.search(p,url)

        if result:

            return result.group(1)


    return None





# =========================
# 댓글 수집
# =========================

def get_comments(video_id):

    comments=[]


    request = youtube.commentThreads().list(

        part="snippet",

        videoId=video_id,

        maxResults=100,

        textFormat="plainText"

    )



    while request:


        response=request.execute()


        for item in response["items"]:

            text=(

                item["snippet"]

                ["topLevelComment"]

                ["snippet"]

                ["textDisplay"]

            )


            comments.append(text)



        token=response.get(
            "nextPageToken"
        )


        if token:

            request=youtube.commentThreads().list(

                part="snippet",

                videoId=video_id,

                maxResults=100,

                pageToken=token,

                textFormat="plainText"

            )


        else:

            break



        if len(comments)>=1000:

            break



    return comments





# =========================
# 단어 추출
# =========================

def extract_words(comments):

    stopwords={

        "영상",
        "진짜",
        "너무",
        "정말",
        "그냥",
        "댓글",
        "사람",
        "생각",
        "ㅋㅋ",
        "ㅎㅎ",
        "입니다",
        "하는"

    }



    words=[]



    for text in comments:


        text=re.sub(

            "[^가-힣 ]",

            "",

            text

        )


        for word in text.split():


            if len(word)>=2 and word not in stopwords:

                words.append(word)



    return words





# =========================
# 워드클라우드
# =========================

def make_wordcloud(words):


    wc = WordCloud(

        font_path=get_korean_font(),

        background_color="white",

        width=1000,

        height=600,

        max_words=100

    )


    return wc.generate_from_frequencies(

        Counter(words)

    )





# =========================
# 감정 분석
# =========================

def analyze_sentiment(comments):

    positive=0
    negative=0
    neutral=0



    for text in comments:


        score=sentiment.polarity_scores(text)["compound"]



        if score>0.05:

            positive+=1


        elif score<-0.05:

            negative+=1


        else:

            neutral+=1



    return positive,negative,neutral





# =========================
# 화면
# =========================

st.title(
    "🎬 YouTube 댓글 심층 분석 AI"
)


url=st.text_input(
    "유튜브 링크 입력"
)



if st.button("🔍 분석 시작"):


    video_id=get_video_id(url)



    if not video_id:

        st.error(
            "유튜브 링크가 올바르지 않습니다."
        )

        st.stop()



    with st.spinner(
        "댓글 분석 중..."
    ):


        comments=get_comments(
            video_id
        )



    if not comments:

        st.warning(
            "댓글이 없습니다."
        )

        st.stop()



    st.success(
        f"{len(comments)}개 댓글 분석 완료"
    )



    # 댓글

    st.subheader(
        "💬 댓글"
    )


    st.dataframe(

        pd.DataFrame(
            comments,
            columns=["댓글"]
        ),

        use_container_width=True

    )



    # 감정

    st.subheader(
        "😊 감정 분석"
    )


    p,n,u=analyze_sentiment(
        comments
    )


    a,b,c=st.columns(3)


    a.metric(
        "긍정",
        p
    )

    b.metric(
        "부정",
        n
    )

    c.metric(
        "중립",
        u
    )



    # 워드클라우드

    st.subheader(
        "☁️ 한글 워드클라우드"
    )


    words=extract_words(
        comments
    )


    if words:


        img=make_wordcloud(
            words
        )


        fig,ax=plt.subplots(
            figsize=(10,6)
        )


        ax.imshow(
            img,
            interpolation="bilinear"
        )


        ax.axis("off")


        st.pyplot(fig)



    # 키워드

    st.subheader(
        "🔥 TOP 키워드"
    )


    st.table(

        pd.DataFrame(

            Counter(words)
            .most_common(20),

            columns=[
                "키워드",
                "횟수"
            ]

        )

    )
