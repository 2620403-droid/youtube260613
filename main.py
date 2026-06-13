import streamlit as st
from googleapiclient.discovery import build

import pandas as pd
import re
import os

from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer



# =========================
# 기본 설정
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
        "Streamlit Secrets에 YOUTUBE_API_KEY를 추가하세요."
    )

    st.stop()



youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)


analyzer = SentimentIntensityAnalyzer()



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

        result=re.search(p,url)

        if result:

            return result.group(1)


    return None




# =========================
# 댓글 가져오기
# =========================

def get_comments(video_id):

    comments=[]


    request=youtube.commentThreads().list(

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
# 한국어 단어 추출
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
        "오늘",
        "보고",
        "ㅋㅋ",
        "ㅎㅎ",
        "입니다"

    }



    words=[]



    for text in comments:


        text=re.sub(

            "[^가-힣 ]",

            "",

            text

        )


        for word in text.split():


            if (

                len(word)>=2

                and word not in stopwords

            ):

                words.append(word)



    return words




# =========================
# 폰트
# =========================

def get_font():


    font="NanumGothic.ttf"


    if os.path.exists(font):

        return font


    return None





# =========================
# 워드클라우드
# =========================

def make_wordcloud(words):


    wc=WordCloud(

        font_path=get_font(),

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

def emotion_analysis(comments):


    positive=0

    negative=0

    neutral=0



    for text in comments:


        score=analyzer.polarity_scores(text)["compound"]



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


st.write(
"""
유튜브 댓글을 분석합니다.

✔ 댓글 수집  
✔ 감정 분석  
✔ 키워드 분석  
✔ 한글 워드클라우드
"""
)



url=st.text_input(
    "유튜브 링크 입력"
)



if st.button("🔍 분석 시작"):


    video_id=get_video_id(url)



    if not video_id:


        st.error(
            "유튜브 링크 형식이 잘못되었습니다."
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
            "댓글을 찾지 못했습니다."
        )

        st.stop()



    st.success(
        f"{len(comments)}개 댓글 분석 완료"
    )



    df=pd.DataFrame(

        comments,

        columns=["댓글"]

    )



    with st.expander(
        "댓글 보기"
    ):

        st.dataframe(
            df,
            use_container_width=True
        )



    # 감정

    st.subheader(
        "😊 감정 분석"
    )


    p,n,u=emotion_analysis(
        comments
    )


    c1,c2,c3=st.columns(3)


    c1.metric(
        "긍정",
        p
    )


    c2.metric(
        "부정",
        n
    )


    c3.metric(
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



    if words and get_font():


        image=make_wordcloud(
            words
        )


        fig,ax=plt.subplots(
            figsize=(10,6)
        )


        ax.imshow(
            image,
            interpolation="bilinear"
        )


        ax.axis(
            "off"
        )


        st.pyplot(fig)



    elif not get_font():


        st.error(
            "NanumGothic.ttf 파일이 없습니다."
        )



    else:


        st.info(
            "분석할 단어가 부족합니다."
        )



    # TOP 키워드

    st.subheader(
        "🔥 키워드 TOP 20"
    )


    keyword=pd.DataFrame(

        Counter(words).most_common(20),

        columns=[
            "키워드",
            "횟수"
        ]

    )


    st.table(keyword)
