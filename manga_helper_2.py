#coding:utf-8

import os
import PyV8
import urllib2, urllib
import re
import threading, Queue, time, random
from sgmllib import SGMLParser
import socket


root_url_img = "http://imgfast.dmzj.com/"
url_root = "http://manhua.dmzj.com"

#图片名称规则
reg_name = re.compile(r"g_comic_name\s=\s\"([^\"]+)\"")
#图片列表规则
reg_img_list = re.compile(r"eval(.+)")
#图片类型规则
reg_img_type = re.compile(r"(\w+)")
#下载目录
path_cur = os.path.abspath(".")

js_cxt = PyV8.JSContext()
		
#socket.setdefaulttimeout(10)#设置超时10s

#解析卷
class ParserChapter(SGMLParser):
	def reset(self):
		SGMLParser.reset(self)

		self.name = ""
		self.chapter = []
		self.url = []
		self.chapter_url = None

		self.test_ul = 0
		self.test_li = 0
		self.test_a = 0
		self.test_div = 0

	def start_div(self, attrs):
		for k, v in attrs:
			if k == "class" and v == "cartoon_online_border":
				self.test_div = 1

			if k == "class" and v == "clearfix" and self.test_div == 1:
				self.test_div = 2

	def start_ul(self, attrs):
		if self.test_div == 1:
			self.test_ul = 1

	def start_li(self, attrs):
		if self.test_ul == 1:
			self.test_li = 1

	def start_a(self, attrs):
		if self.test_li == 1:
			for k, v in attrs:
				if k != "title" and k != "href":
					return

				if k == "href":
					self.url.append(url_root + v)

				self.test_a = 1

	def end_a(self):
		if self.test_li == 1:
			self.test_a = 0

	def end_li(self):
		if self.test_ul == 1:
			self.test_li = 0

	def end_ul(self):
		if self.test_div == 1:
			self.test_ul = 0

	def end_div(self):
		if self.test_div:
			self.test_div -= 1

	def handle_data(self, data):
		if self.test_a:
			self.chapter.append(data)

	def get_chapter_url(self):
		self.chapter_url = zip(self.chapter, self.url)
		return self.chapter_url

	def get_name(self, content):
		return reg_name.findall(content)[0]

#解析器
class Fetch:
	def __init__(self):
		pass

	@classmethod
	def fetch_img(self, content):
		js_cxt.enter()
		js = "eval" + reg_img_list.findall(content)[0] + ";eval(pages)"
		rs = list(js_cxt.eval(js))
		js_cxt.leave()
		return map(lambda x : root_url_img + x, rs)

	@classmethod
	def fetch_name(self, content):
		return reg_name.findall(content)[0]

	@classmethod
	def fetch_type(self, content):
		return reg_img_type.findall(content)[-1]

#下载任务块
class Block:
	def __init__(self, task, img_url, location):
		self.task = task
		self.img_url = img_url
		self.location = location

	def count(self):
		self.task.count()

#下载任务
class Task:
	def __init__(self, manga, selection, queue, queue2):
		#任务对应的漫画对象
		self.manga = manga
		#任务选择
		self.selection = selection
		#任务对应的ui组件
		self.ui = None 
		#任务块
		self.blocks = [] 
		#已下载的页数
		self.downloaded = 0
		#总页数
		self.page_num = 0
		#线程容器
		self.queue = queue
		#低优先级线程容器
		self.queue2 = queue2

	#下载计数及ui刷新
	def count(self):
		self.ui.count()

	def run_task(self):
		map(lambda x : self.queue.put(x), self.blocks)

	#启动下载任务
	def parse(self):
		path_manga = os.path.join(path_cur, self.manga.name).decode("utf-8")
		if not os.path.exists(path_manga):
			os.mkdir(path_manga)
		else:
			return False
		for chapter, url in self.selection:
			path_chapter = os.path.join(path_manga.encode("utf-8"), chapter).decode("utf-8")
			if not os.path.exists(path_chapter):
				os.mkdir(path_chapter)
			socket = urllib2.urlopen(url)
			content = socket.read()
			socket.close()
			img_urls = Fetch.fetch_img(content)
			self.page_num += len(img_urls)
			for i, img_url in enumerate(img_urls):
				pic_name = ".".join([str(i + 1), Fetch.fetch_type(img_url)]) 
				location = os.path.join(path_chapter, pic_name)
				self.blocks.append(Block(self, img_url, location))

		return True

#漫画类
class Manga:
	def __init__(self, url):
		#漫画首页url
		self.url = url
		#漫画名
		self.name = None
		#漫画章节和url
		self.chapter_url = []

	def parse(self):
		socket = urllib2.urlopen(self.url) 
		content = socket.read()
		socket.close()
		#解析漫画名
		self.name = Fetch.fetch_name(content)
		#解析章节
		chapter_parser = ParserChapter()
		chapter_parser.feed(content)
		self.chapter_url = chapter_parser.get_chapter_url()

class Thread(threading.Thread):
	def __init__(self, queue, queue2, handler):
		threading.Thread.__init__(self)
		self.queue = queue
		self.queue2 = queue2
		self.handler = handler

	def run(self):
		time.sleep(1)
		while True:
			if (self.queue.qsize() > 0 or self.queue2.qsize() == 0):
				self.handler(self.queue.get())
			else:
				print "get from queue2"
				self.handler(self.queue2.get())

#下载处理器
def handler_download(block):
	try:
		urllib.urlretrieve(block.img_url, block.location)
		print "queue.qsize():", block.task.queue.qsize(), "queue2.qsize():", block.task.queue2.qsize()
		block.count()
	except Exception, e:
		block.task.queue2.put(block)
