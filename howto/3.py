# -*- coding: utf-8 -*-
from chatterbot import ChatBot
from pythainlp.tokenize import word_tokenize
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.comparisons import thai
from pythainlp import word_tokenize
'''def levenshtein_distance():
    return 0'''
chatbot = ChatBot(
    'Fah', # ชื่อแชตบ็อต
    storage_adapter='chatterbot.storage.SQLStorageAdapter', # กำหนดการจัดเก็บ ในที่นี้เลือก chatterbot.storage.SQLStorageAdapter เก็บเป็น Sqllite
    database='fah.sqlite3', # ที่ตั้งฐานข้อมูล
    statement_comparison_function=thai
)
chatbot.set_trainer(ChatterBotCorpusTrainer) # กำหนดให้ Train จากชุดข้อมูลของ Chatterbot

chatbot.train(
    "chatterbot.corpus.thai"
) # เรียกใช้ชุดข้อมูล chatterbot.corpus.english
text=""
while True:
    text=input("Text : ")
    if text=="exit":
        break
    response = chatbot.get_response(text)
    print(response)