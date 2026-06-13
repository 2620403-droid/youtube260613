import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt

from konlpy.tag import Okt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# -----------------------------
# 설정
# -----------------------------

st.set_page_config(
    page_title="YouTube 댓글 분석 AI",
    page_icon="🎬",
    layout="wide"
)


# API KEY
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except:
    st.error("Streamlit Secrets에 YOUTUBE_API_KEY를 등록해주세요.")
    st.stop()


youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)


okt = Okt()
sentiment = SentimentIntensityAnalyzer()


# -----------------------------
# 영상 ID 추출
# -----------------------------

def get_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"youtube\.com/shorts/([^?]+)"
    ]

    for p in patterns:
        result = re.search(p, url)

        if result:
            return result.group(1)

    return None



# -----------------------------
# 댓글 가져오기
# -----------------------------

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

            text=item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

            comments.append(text)


        if "nextPageToken" in response:

            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=response["nextPageToken"],
                textFormat="plainText"
            )

        else:
            break


        if len(comments)>1000:
            break


    return comments




# -----------------------------
# 한국어 형태소 분석
# -----------------------------

def extract_words(texts):

    words=[]


    stopwords=set([
        "영상",
        "진짜",
        "너무",
        "정말",
        "ㅋㅋ",
        "ㅎㅎ",
        "그냥",
        "보고",
        "하는",
        "입니다",
        "같아요",
        "제가"
    ])


    for t in texts:

        nouns=okt.nouns(t)


        for n in nouns:

            if len(n)>1 and n not in stopwords:
                words.append(n)


    return words




# -----------------------------
# 워드클라우드
# -----------------------------

def make_wordcloud(words):

    wc=WordCloud(
        font_path="/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        background_color="white",
        width=1000,
        height=600
    )


    image=wc.generate_from_frequencies(
        Counter(words)
    )


    return image




# -----------------------------
# 감정 분석
# -----------------------------

def analyze_sentiment(comments):

    positive=0
    negative=0
    neutral=0


    for c in comments:

        score=sentiment.polarity_scores(c)["compound"]


        if score>0.05:
            positive+=1

        elif score<-0.05:
            negative+=1

        else:
            neutral+=1


    return positive,negative,neutral




# -----------------------------
# UI
# -----------------------------


st.title("🎬 YouTube 댓글 심층 분석 AI")

st.write(
"""
유튜브 링크를 입력하면 댓글을 분석합니다.

- 한국어 키워드 분석
- 워드클라우드
- 감정 분석
- 인기 의견 파악
"""
)


url=st.text_input(
    "유튜브 링크 입력"
)



if st.button("댓글 분석 시작"):


    video_id=get_video_id(url)


    if not video_id:

        st.error("올바른 유튜브 링크가 아닙니다.")

        st.stop()



    with st.spinner("댓글 수집 및 분석 중..."):


        comments=get_comments(video_id)


    if len(comments)==0:

        st.warning(
            "댓글을 찾을 수 없습니다."
        )

        st.stop()



    df=pd.DataFrame(
        {
            "댓글":comments
        }
    )


    st.success(
        f"{len(comments)}개의 댓글 분석 완료"
    )



    # 댓글 보기

    with st.expander("댓글 원문 보기"):

        st.dataframe(df)



    # 감정

    pos,neg,neu=analyze_sentiment(comments)


    st.subheader("😊 감정 분석")


    col1,col2,col3=st.columns(3)


    col1.metric(
        "긍정",
        pos
    )

    col2.metric(
        "부정",
        neg
    )

    col3.metric(
        "중립",
        neu
    )



    # 키워드

    words=extract_words(comments)


    st.subheader("☁️ 한국어 워드클라우드")


    if words:

        img=make_wordcloud(words)


        fig,ax=plt.subplots(figsize=(10,6))

        ax.imshow(
            img,
            interpolation="bilinear"
        )

        ax.axis("off")


        st.pyplot(fig)


    else:

        st.info(
            "분석 가능한 단어가 부족합니다."
        )



    # TOP 키워드


    st.subheader("🔥 주요 키워드 TOP 20")


    count=Counter(words)


    keyword_df=pd.DataFrame(
        count.most_common(20),
        columns=[
            "키워드",
            "등장횟수"
        ]
    )


    st.table(keyword_df)
