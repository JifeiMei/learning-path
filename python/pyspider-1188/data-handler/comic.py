#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2015-03-03 13:14:54
# Project: test

import re
from urlparse import urljoin, urlparse, urlunparse, urlsplit, urlunsplit
import sqlite3
import ast
import MySQLdb
import logging
import pinyin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from declarative import  Base, Video, VideoInfo, Category, PlaySource, Specicalty
from sqlalchemy.orm.exc import NoResultFound

def initSession():
    engine = create_engine('mysql+mysqldb://test:test@192.168.2.50/1188test?charset=utf8&use_unicode=0')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

def searchVideo(session,movie, video_type_id):
    try:
        movie = session.query(Video).filter(Video.orig_id == int(movie['orig_id'])).filter(Video.video_type_id == video_type_id).one()
    except Exception, e:
        raise e
    return movie

def saveMovie(session, movie):
    #处理rating和runtime
    if not movie['rating']:
        movie['rating'] = '0'
    rating = re.search('\d+(\.?\d?)*', movie['rating']).group(0)
    if not movie['runtime']:
        movie['runtime'] = '000'
    if not movie['year']:
        movie['year'] = 0
    
    video = Video(name=movie['title'].decode('unicode-escape'), 
            rating= float(rating) ,
            director=movie['director'].decode('unicode-escape'), 
            runtime = int(movie['runtime'].decode('unicode-escape')[:-2]),
            year = int(movie['year']),
            location = movie['location'].decode('unicode-escape'),
            lang = movie['lang'].decode('unicode-escape'),
            orig_id = int(movie['orig_id']),
            video_type_id = 1
        )
    session.add(video)
    return video

def searchAndSaveMovie(session, movie, video_type_id):
    if not movie['title']:
        return None

    try:
        movie = searchVideo(session, movie, video_type_id)
    except NoResultFound, e:
        movie = saveMovie(session, movie)
    except Exception, e:
        raise e
    return movie


def saveVideoInfo(session, movie, savedMovieObj):
    if savedMovieObj is None:
        return None

    try:
        # 查找是否已经存在
        videoInfoObj = session.query(VideoInfo).filter(VideoInfo.video == savedMovieObj).one()
        return videoInfoObj
    except NoResultFound, e:
        actors = ''
        if len(movie['casting']) > 0:
            actorList = [x.decode('unicode-escape') for x in movie['casting']]
            actors = ', '.join(actorList)

        videoInfoObj = VideoInfo(introduction=movie['introduction'].decode('unicode-escape'),
                poster_image = movie['poster_image'],
                small_image = movie['small_image'],
                actors= actors,
                video = savedMovieObj
            )
        session.add(videoInfoObj)
        return videoInfoObj
    except Exception, e:
        logging.error(e)
        raise e
    

def searchAndLinkCategory(sesstion, movie, savedMovieObj, video_type_id):
    if savedMovieObj is None:
        return None
    cats = movie['categories']
    for catName in cats:
        try:
            # 查找已有的
            catObj = session.query(Category).filter(Category.name == catName.decode('unicode-escape')).filter(Category.video_type_id == video_type_id).one()
            savedMovieObj.categories.append(catObj)
        except NoResultFound, e:
            # if not found, then save the cat, and associate the relations
            catObj = Category(name=catName.decode('unicode-escape'),
                    video_type_id=video_type_id,
                    url_rewrite = pinyin.get(catName.decode('unicode-escape')) or '',
                    is_hot = 0,
                    is_displayed = 0
                )
            session.add(catObj)
            savedMovieObj.categories.append(catObj)
        except Exception, e:
            logging.error(e)
            continue

def searchAndLinkPlaySource(sesstion, movie, savedMovieObj, video_type_id):
    if savedMovieObj is None:
        return None
    play_sources = movie['play_source']
    for api_name in play_sources:
        try:
            playSource = session.query(PlaySource).filter(PlaySource.api_name == api_name).filter(PlaySource.video_id == savedMovieObj.id).one()
        except NoResultFound, e:
            playSource = PlaySource(api_name=api_name,
                    url=play_sources[api_name],
                    video=savedMovieObj
                )
            session.add(playSource)
        except Exception, e:
            logging.error(e)
            raise e

def searchAndLinkSpecialty(sesstion, movie, savedMovieObj, video_type_id):
    if savedMovieObj is None:
        return None
    seps = movie['specialties']
    for sep in seps:
        try:
            sepObj = session.query(Specicalty).filter(Specicalty.name == sep.decode('unicode-escape')).filter(Specicalty.video_type_id == video_type_id).one()
            savedMovieObj.specialties.append(sepObj)
        except NoResultFound, e:
            # if not found, then save the sep, and associate the relations
            sepObj = Specicalty(name=sep.decode('unicode-escape'),
                    video_type_id=video_type_id
                )
            session.add(sepObj)
            savedMovieObj.specialties.append(sepObj)
        except Exception, e:
            logging.error(e)
            raise e

def doesVideoExist(session, video_id):
    pass

session = initSession()
with sqlite3.connect('result.db') as db:
    cursor = db.cursor()
    cursor.execute('''SELECT taskid, result from resultdb_movie limit 0, 300''')
    allRows = cursor.fetchall()
    i = 0
    for row in allRows:
        try:
            movie = ast.literal_eval(row[1])
            # 保存video, 如果已经存在就返回搜索到的Video对象
            savedMovieObj = searchAndSaveMovie(session, movie, 1)
            # 保存VideoInfo
            saveVideoInfo(session, movie, savedMovieObj)
            #保存并关联category
            searchAndLinkCategory(session, movie, savedMovieObj, 1)
            #保存并关联play source
            searchAndLinkPlaySource(session, movie, savedMovieObj, 1)
            # 保存并关联sepcialty
            searchAndLinkSpecialty(session, movie, savedMovieObj, 1)
            
            i += 1
            if i % 200 == 0:
                session.commit()
        except Exception, e:
            logging.error('Error: %s, taskid : %s',e, row[0])
            #logging.error('task id is  %s, eval error ', row[0])
    session.commit()
    


# try:
#     db = MySQLdb.connect('192.168.2.50', 'test', 'test', 'test')
#     cursor = db.cursor()
#     cursor.execute(""" SELECT * from api """)
#     for x in cursor.fetchall():
#         print x[1]

# except Exception, e:
#     print e

