# -*- coding: utf-8 -*-
from pythainlp import word_tokenize # ทำการเรียกตัวตัดคำ
from pythainlp.word_vector import thai2vec # ทำการเรียก thai2vec
from sklearn.metrics.pairwise import cosine_similarity  # ใช้หาค่าความคล้ายคลึง
import numpy as np
model=thai2vec.get_model() # ดึง model ของ thai2vec มาเก็บไว้ในตัวแปร model
def sentence_vectorizer(ss,dim=300,use_mean=True): # ประกาศฟังก์ชัน sentence_vectorizer
    s = word_tokenize(ss)
    vec = np.zeros((1,dim))
    for word in s:
        if word in model.wv.index2word:
            vec+= model.wv.word_vec(word)
        else: pass
    if use_mean: vec /= len(s)
    return vec
def sentence_similarity(s1,s2):
    return cosine_similarity(sentence_vectorizer(str(s1)),sentence_vectorizer(str(s2)))
print(sentence_similarity("ผมเป็นนักศึกษาเรียนที่มหาวิทยาลัยขอนแก่น","ผมเป็นนักศึกษามหาวิทยาลัยขอนแก่น"))