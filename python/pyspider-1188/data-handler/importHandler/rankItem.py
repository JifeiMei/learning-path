#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2015-03-03 13:14:54
# Project: test

import re
from urlparse import urljoin, urlparse, urlunparse, urlsplit, urlunsplit
import sqlite3
import ast
import MySQLdb
import logging,logger
import pinyin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from declarative import  Base, Video, VideoInfo, Category, PlaySource, Specicalty, RankItem, IndexItem
from sqlalchemy.orm.exc import NoResultFound

myLogger = logging.getLogger('v1188ys.importer.rank_item')
def initSession():
    engine = create_engine('mysql+mysqldb://test:test@172.16.1.19/1188test?charset=utf8&use_unicode=0')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

def searchVideo(session,orig_id, video_type_id):
    try:
        video = session.query(Video).filter(Video.orig_id == int(orig_id)).filter(Video.video_type_id == int(video_type_id)).one()
    except NoResultFound, e:
        raise e
    except Exception, e:
        print 'SearhVideo Error'
        raise e
    return video


def searchAndSaveRank(session, rankObjs):
    if not len(rankObjs):
        return None

    for rank in rankObjs:
        try:
            video = searchVideo(session, rank['orig_id'], rank['video_type_id'])
            rankItem = RankItem(video=video,
                    position = rank['position'],
                    section = rank['section'].decode('unicode-escape'),
                    video_type_id = rank['video_type_id']
                )
            session.add(rankItem)
        except NoResultFound, e:
            #print 'cannot find video whose orig_id=%s, video_type_id=%s ' % (rank['orig_id'], rank['video_type_id'])
            continue
        except Exception, e:
            raise e

def start():
    session = initSession()
    with MySQLdb.connect('172.16.1.248', 'qiye_dev', 'qiye..dev', '1188ys_resultdb') as cursor:
        #cursor = db.cursor()
        cursor.execute('''SELECT taskid, result from rank_item''')
        allRows = cursor.fetchall()
        i = 0
        for row in allRows:
            try:
                rankObjs = ast.literal_eval(row[1])
                # 根据orig_id和video_type_id来查询现在的id。保存。
                searchAndSaveRank(session, rankObjs)
                i += 1
                if i % 200 == 0:
                    session.commit()
            except Exception, e:
                myLogger.error('Error: %s, taskid : %s',e, row[0])
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

