#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
$Id$
"""
import os, sys

from twisted.internet.protocol import Factory, ProcessProtocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver

from mbco.videohost.local_settings import TRANSCODE_PORT


base_folder = os.path.dirname(__file__)


class SpawnProtocol(ProcessProtocol):

    def __init__(self, file_name):
        self.file_name = file_name
        
    def connectionMade(self):
        print 'start: %s' % (self.file_name)

    def errReceived(self, data):
        print 20*"*"
        print "    ERR RECEIVED (%s):" % self.file_name, data
        print 20*"*"
    
    def processEnded(self, status):
        print 'end: %s (status=%s)' % (self.file_name, status.value.exitCode)
        # TODO: если статус отличен от нуля то переставить в очередь (итак несколько раз)
        g_manager.release()
        

class Server(LineReceiver):

    def lineReceived(self, line):
        u""" получает строку состояющую из параметров разделённых '***' 
        param1 - имя оригинального файла
        param2 - имя авто-скрина
        param3 - account-id
        param4 - video-id
        param5 - need_hls
        """
        fname = line
        g_manager.add_file(fname)
        

class Manager:
    counter = 0
    files = None

    def __init__(self):
        self.files = []
        self.printStat()

    def printStat(self):
        print "STAT: counter(%s) wait(%d)" % (self.counter, len(self.files))
        sys.stdout.flush()
        return reactor.callLater(5, self.printStat)
    

    def add_file(self, fname):
        u"добавляет файл в очередь"
        self.files.append(fname)
        self.try_precode()

            
    def release(self):
        u"информирует, что один процесс завершился"
        self.counter = self.counter - 1
        self.try_precode()
        
            
    def try_precode(self):
        print "IN WAIT: ", len(self.files)
        
        # если достигли лимита, то гуляем
        if self.counter == MAX_COUNT:
            return
        
        # если файлов нет, то гуляем
        if not self.files:
            return
        
        fname = self.files.pop(0)
        self.counter += 1
        self.make_precod(fname)
        reactor.callLater(1, self.try_precode)
        
        
    def make_precod(self, fname):
        u"запускает прекодирующий скрипт"
        # разделяем имя файла от имени тумбы
        input_file_name, thumb_name, account_id, video_id, need_hls  = fname.split('***')
        

        transcode_script = os.path.join(base_folder, 'transcode_one.sh')
        cmd = [transcode_script, input_file_name, thumb_name, account_id, video_id, need_hls]
        
        sp = SpawnProtocol(input_file_name)
        p = reactor.spawnProcess(sp, cmd[0], cmd, env=os.environ)
        
        

g_manager = Manager()
factory = Factory()
factory.protocol = Server

MAX_COUNT = 3

reactor.listenTCP(TRANSCODE_PORT, factory, interface='127.0.0.1')
reactor.run()

