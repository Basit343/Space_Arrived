import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import base64
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode, ClientSettings
import av
import numpy as np

load_dotenv()
api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=api_key)

def get_answer(messages, custom_prompt, language):
    system_message = [{
        "role": "system", 
        "content": f"Respond in {language}."
    }]
    messages = system_message + messages
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        timeout=5,
        messages=messages
    )
    return response.choices[0].message.content

def speech_to_text(audio_data):
    with open(audio_data, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            response_format="text",
            file=audio_file
        )
    return transcript

def text_to_speech(input_text, voice):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=input_text
    )
    webm_file_path = "temp_audio_play.mp3"
    with open(webm_file_path, "wb") as f:
        response.stream_to_file(webm_file_path)
    return webm_file_path

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_data = None

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.audio_data = frame.to_ndarray()
        return frame

# Streamlit interface
st.title("Reactive Space Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Add inputs for initial message, voice selection, and custom prompt
initial_message = st.text_input("Initial Message", value="How can I help you?")
voice = st.selectbox("Select Voice", ["onyx", "echo", "alloy", "fable","shimmer","nova"])
language = st.selectbox("Select Language", ["English", "Spanish", "French", "German", "Chinese"])

# Default custom prompt without the language selection visible to the user
default_custom_prompt = """Hey {Lead Name}, this is Basit Ali calling, How are you doing today? I am good, thanks for asking....... so {lead name} the purpose of my call is in response to your recent FB Ads inquiry where you were seeking further information surrounding MetaVerse services…
Do you remember booking the appointment?
yes : Move on
No: Remind them that they clicked on a FB advertisement and provided their information as they were interested in Metaverse and how it could help them.
So (Name), once again my name is (name) and I represent MetaVerse specialist, Reactive Space. We develop and implement MetaVerse solutions globally. Based on your request do you have 15 mins now for a quick conversation so we can learn more about your requirements?
Yes: Move on
No: Seek a callback time or confirm they are still interested.
Awesome, As I said I just need to ask a few questions to see if we might be a good fit for you and then I will set up a service overview call with a team consultant.... So let's kick off.
Question 1:
Tell me a little more about yourself, your current role/industry and your motivations
For investing in MetaVerse?
Response 1:
Question 2:
If you were to set a goal or return you would like to achieve from investing in a MetaVerse solution over the next 12 months what number would you set for yourself or Business?
Response 2:
Note: Confirm the value back to them, example I want to sell 10 products at 10k per product over the next 12 months. This means they want to achieve 100k in sales over the first year.
Rebuttal to question 2:
It’s really important we have an understanding of your goals so we can help design the right solution to help you achieve that goal, so is there a revenue goal you have?"""

custom_prompt = st.text_area("Custom Prompt", value=default_custom_prompt)

# Add a "Call" button
if st.button("Call"):
    initial_audio_path = text_to_speech(initial_message, voice)
    st.session_state.initial_audio_path = initial_audio_path
    st.session_state.messages.append({"role": "assistant", "content": initial_message})

# Play the initial greeting audio if it exists
if "initial_audio_path" in st.session_state and st.session_state.initial_audio_path:
    autoplay_audio(st.session_state.initial_audio_path)
    os.remove(st.session_state.initial_audio_path)
    del st.session_state.initial_audio_path

footer_container = st.container()

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# WebRTC Streamer
webrtc_ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDRECV,
    client_settings=ClientSettings(
        media_stream_constraints={
            "audio": True,
            "video": False
        },
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
    ),
    audio_processor_factory=AudioProcessor
)

if webrtc_ctx.state.playing:
    audio_processor = webrtc_ctx.audio_processor
    if audio_processor and audio_processor.audio_data is not None:
        audio_bytes = audio_processor.audio_data.tobytes()
        webm_file_path = "temp_audio.webm"
        with open(webm_file_path, "wb") as f:
            f.write(audio_bytes)
        transcript = speech_to_text(webm_file_path)
        if transcript:
            st.session_state.messages.append({"role": "user", "content": transcript})
            with st.chat_message("user"):
                st.write(transcript)
            os.remove(webm_file_path)

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Thinking🤔..."):
            final_response = get_answer(st.session_state.messages, custom_prompt, language)
        with st.spinner("Generating audio response..."):
            audio_file = text_to_speech(final_response, voice)
            autoplay_audio(audio_file)
        st.write(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file)

# Float the footer container at the bottom of the page
footer_container.float("bottom: 0rem;")


# import streamlit as st
# import openai
# from dotenv import load_dotenv
# import os
# import base64
# from audio_recorder_streamlit import audio_recorder
# from streamlit_float import float_init
# from gtts import gTTS  # Import gTTS for text-to-speech

# # Load environment variables
# load_dotenv()
# api_key = st.secrets["OPENAI_API_KEY"]

# # Configure OpenAI
# openai.api_key = api_key

# def get_answer(messages, custom_prompt):
#     system_message = [{
#         "role": "system", 
#         "content": custom_prompt
#     }]
#     messages = system_message + messages
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         temperature=0.7,
#         messages=messages
#     )
#     return response.choices[0].message['content']

# def speech_to_text(audio_data):
#     with open(audio_data, "rb") as audio_file:
#         transcript = openai.Audio.transcribe(
#             model="whisper-1",
#             file=audio_file
#         )
#     return transcript['text']

# def text_to_speech(input_text, voice):
#     tts = gTTS(text=input_text, lang='en')
#     file_path = "temp_audio.mp3"
#     tts.save(file_path)
#     return file_path

# def autoplay_audio(file_path: str):
#     if os.path.exists(file_path):
#         with open(file_path, "rb") as f:
#             data = f.read()
#         b64 = base64.b64encode(data).decode("utf-8")
#         md = f"""
#         <audio autoplay>
#         <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
#         </audio>
#         """
#         st.markdown(md, unsafe_allow_html=True)
#         os.remove(file_path)
#     else:
#         st.error("File not found for autoplay.")

# # Streamlit interface
# float_init()
# st.title("Reactive Space Agent")

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Add inputs for initial message, voice selection, and custom prompt
# initial_message = st.text_input("Initial Message", value="How can I help you?")
# voice = st.selectbox("Select Voice", ["onyx", "echo", "alloy", "fable","shimmer","nova"])
# custom_prompt = st.text_area("Custom Prompt", value="""you can only respond in English. Hey {Lead Name}, this is Basit Ali calling, How are you doing today? I am good, thanks for asking....... so {lead name} the purpose of my call is in response to your recent FB Ads inquiry where you were seeking further information surrounding MetaVerse services…
# Do you remember booking the appointment?
# yes : Move on
# No: Remind them that they clicked on a FB advertisement and provided their information as they were interested in Metaverse and how it could help them.
# So (Name), once again my name is (name) and I represent MetaVerse specialist, Reactive Space. We develop and implement MetaVerse solutions globally. Based on your request do you have 15 mins now for a quick conversation so we can learn more about your requirements?
# Yes: Move on
# No: Seek a callback time or confirm they are still interested.
# Awesome, As I said I just need to ask a few questions to see if we might be a good fit for you and then I will set up a service overview call with a team consultant.... So let's kick off.
# Question 1:
# Tell me a little more about yourself, your current role/industry and your motivations
# For investing in MetaVerse?
# Response 1:
# Question 2:
# If you were to set a goal or return you would like to achieve from investing in a MetaVerse solution over the next 12 months what number would you set for yourself or Business?
# Response 2:
# Note: Confirm the value back to them, example I want to sell 10 products at 10k per product over the next 12 months. This means they want to achieve 100k in sales over the first year.
# Rebuttal to question 2:
# It’s really important we have an understanding of your goals so we can help design the right solution to help you achieve that goal, so is there a revenue goal you have?""")

# # Add a "Call" button
# if st.button("Call"):
#     initial_audio_path = text_to_speech(initial_message, voice)
#     st.session_state.initial_audio_path = initial_audio_path
#     st.session_state.messages.append({"role": "assistant", "content": initial_message})

# # Play the initial greeting audio if it exists
# if "initial_audio_path" in st.session_state and st.session_state.initial_audio_path:
#     autoplay_audio(st.session_state.initial_audio_path)
#     del st.session_state.initial_audio_path

# footer_container = st.container()

# # Display previous messages
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.write(message["content"])

# audio_bytes = audio_recorder()
# if audio_bytes:
#     with st.spinner("Transcribing..."):
#         webm_file_path = "temp_audio.mp3"
#         with open(webm_file_path, "wb") as f:
#             f.write(audio_bytes)
#         transcript = speech_to_text(webm_file_path)
#         if transcript:
#             st.session_state.messages.append({"role": "user", "content": transcript})
#             with st.chat_message("user"):
#                 st.write(transcript)
#             os.remove(webm_file_path)

# if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking🤔..."):
#             final_response = get_answer(st.session_state.messages, custom_prompt)
#         with st.spinner("Generating audio response..."):
#             audio_file = text_to_speech(final_response, voice)
#             autoplay_audio(audio_file)
#         st.write(final_response)
#         st.session_state.messages.append({"role": "assistant", "content": final_response})

# # Float the footer container at the bottom of the page
# footer_container.float("bottom: 0rem;")
