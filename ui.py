#coding:utf-8
import wx
import Queue
import manga_helper_2 as MH
import  wx.lib.scrolledpanel as scrolled

#队列
queue = None
#线程池大小
NUM_THREAD = 50
#线程池
thread_pool = []

ui = {}

class App(wx.App):
	def __init__(self, redirect = False):
		wx.App.__init__(self, redirect)
		init_thread_pool()
		frame_main = FrameMain(None, -1, "manga-helper-2") 

	def OnInit(self):
		return True

class ScrollChapter(scrolled.ScrolledPanel):
	def __init__(self, parent, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize):
		scrolled.ScrolledPanel.__init__(self, parent, id, pos, size, wx.BORDER)

		self.sizer = wx.FlexGridSizer(rows = 500, cols = 1, hgap = 0, vgap = 0)
		self.SetSizer(self.sizer)
		self.SetBackgroundColour("white")

	def add_chapter(self, chapters):
		self.sizer.Clear(True)	
		width = 0
		height = 0
		for c in chapters:
			try:
				checkbox = wx.CheckBox(self, -1, c.decode("utf-8"))
				if width == 0 or height == 0:
					width, height = checkbox.GetSize()
				self.sizer.Add(checkbox, 0, wx.LEFT | wx.TOP, 5)
				self.sizer.Layout()
			except Exception, e:
				pass

		self.SetScrollbars(1, 1, width, height * len(chapters) + 3 * (len(chapters) - 1))

class PanelLeft(wx.Panel):
	def __init__(self, parent, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize):
		wx.Panel.__init__(self, parent, id, pos, size)
		self.scroll_1 = ScrollChapter(self, -1, (0, 0), (150, 200))

class PanelMain(wx.Panel):
	def __init__(self, parent, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize):
		wx.Panel.__init__(self, parent, id, pos, size)

		self.ctrl = wx.TextCtrl(self, -1, "", (10, 10), (280, -1))
		self.btn_1 = wx.Button(self, -1, u"链接", (300, 7), (-1, -1))
		self.panel_left = ScrollChapter(self, -1, (10, 50), (150, 230))
		self.checkbox_1 = wx.CheckBox(self, -1, u"全选", (10, 290))
		self.checkbox_2 = wx.CheckBox(self, -1, u"反选", (10, 310))
		self.btn_2 = wx.Button(self, -1, u"下载", (60, 290), (100, 37))

		self.btn_1.Bind(wx.EVT_BUTTON, self.OnLink)

	def OnLink(self, evt):
		manga = MH.Manga(self.ctrl.GetValue())
		manga.parse()
		chapter = [chapter for chapter, url in manga.chapter_url]
		self.panel_left.add_chapter(chapter)

class FrameMain(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title, style = wx.CAPTION | wx.MINIMIZE_BOX | wx.CLOSE_BOX)

		self.panel = PanelMain(self)

		self.Show()
		self.Center()
		self.SetClientSize((400, 335))
		self.Fit()

def init_thread_pool():
	global queue
	queue = Queue.Queue(0)
	map(lambda x : thread_pool.append(MH.Thread(queue, MH.handler_download)), xrange(NUM_THREAD))
	map(lambda x : x.setDaemon(True), thread_pool)
	map(lambda x : x.start(), thread_pool)

if __name__ == "__main__":
	app = App(False)
	app.MainLoop()
