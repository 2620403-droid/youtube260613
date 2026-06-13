import streamlit as st
from googleapiclient.discovery import build

import pandas as pd
import re
from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer



# ==========================
# 기본 설정
# ==========================

st.set_page_config(
    page_title="YouTube 댓글 분석 AI",
    page_icon="🎬",
    layout="wide"
)



# ==========================
# API 설정
# ==========================

try:

    API_KEY = st.secrets["YOUTUBE_API_KEY"]

except:

    st.error(
        "Streamlit Secrets에 YOUTUBE_API_KEY를 입력해주세요."
    )

    st.stop()



youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)


sentiment = SentimentIntensityAnalyzer()



# ==========================
# 영상 ID 찾기
# ==========================

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




# ==========================
# 댓글 수집
# ==========================

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





# ==========================
# 한국어 단어 추출
# ==========================

def extract_words(comments):


    stopwords = {

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



    for comment in comments:


        clean=re.sub(

            "[^가-힣 ]",

            "",

            comment

        )



        for word in clean.split():


            if (

                len(word)>=2

                and word not in stopwords

            ):

                words.append(word)



    return words





# ==========================
# 폰트 찾기
# ==========================

def find_font():


    fonts=fm.findSystemFonts()



    for font in fonts:


        name=font.lower()


        if (

            "nanum" in name

            or "noto" in name

            or "malgun" in name

        ):

            return font



    return None





# ==========================
# 워드클라우드
# ==========================

def make_wordcloud(words):


    font=find_font()



    wc=WordCloud(

        font_path=font,

        background_color="white",

        width=1000,

        height=600,

        max_words=100

    )



    return wc.generate_from_frequencies(

        Counter(words)

    )





# ==========================
# 감정 분석
# ==========================

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





# ==========================
# 화면
# ==========================

st.title(
    "🎬 YouTube 댓글 심층 분석 AI"
)


st.write(
"""
유튜브 영상 댓글을 분석합니다.

기능:
- 댓글 수집
- 감정 분석
- 한국어 키워드 분석
- 한글 워드클라우드
"""
)



url=st.text_input(
    "유튜브 링크 입력"
)



if st.button("🔍 분석 시작"):


    vid=get_video_id(url)



    if not vid:


        st.error(
            "유튜브 링크가 올바르지 않습니다."
        )

        st.stop()



    with st.spinner(
        "댓글 분석 중..."
    ):


        comments=get_comments(vid)



    if len(comments)==0:


        st.warning(
            "댓글을 찾을 수 없습니다."
        )

        st.stop()



    st.success(

        f"{len(comments)}개의 댓글 분석 완료"

    )



    # 댓글 출력

    df=pd.DataFrame(

        {

            "댓글":comments

        }

    )


    with st.expander(
        "댓글 원문 보기"
    ):

        st.dataframe(

            df,

            use_container_width=True

        )




    # 감정

    st.subheader(
        "😊 감정 분석"
    )



    p,n,u=analyze_sentiment(
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


        ax.axis(
            "off"
        )


        st.pyplot(fig)



    else:


        st.info(
            "키워드를 찾지 못했습니다."
        )





    # TOP 키워드

    st.subheader(
        "🔥 인기 키워드 TOP 20"
    )



    top=pd.DataFrame(

        Counter(words)

        .most_common(20),

        columns=[

            "키워드",

            "횟수"

        ]

    )


    st.table(top)
