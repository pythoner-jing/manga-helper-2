#coding:utf-8
import wx
import Queue
import manga_helper_2 as MH
import  wx.lib.scrolledpanel as scrolled

#队列
queue = None
queue2 = None
#线程池大小
NUM_THREAD = 10
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

		self.sizer = wx.FlexGridSizer(rows = 1000, cols = 1, hgap = 0, vgap = 0)
		self.SetSizer(self.sizer)
		self.SetBackgroundColour("white")
		self.checkboxs = []
		self.chapter_urls = None

	def set_chapter(self, chapter_urls):
		self.chapter_urls = chapter_urls
		self.sizer.Clear(True)	
		self.checkboxs = []
		width = 0
		height = 0
		for c, u in chapter_urls:
			try:
				checkbox = wx.CheckBox(self, -1, c.decode("utf-8"))
				self.checkboxs.append(checkbox)
				if width == 0 or height == 0:
					width, height = checkbox.GetSize()
				self.sizer.Add(checkbox, 0, wx.LEFT | wx.TOP, 5)
				self.sizer.Layout()
			except Exception, e:
				pass

		self.SetScrollbars(1, 1, width, height * len(chapter_urls) + 5 * (len(chapter_urls) - 1))

	def select_all(self, value):
		map(lambda x : x.SetValue(value), self.checkboxs)

	def select_reverse(self):
		map(lambda x : x.SetValue(not x.GetValue()), self.checkboxs)

	def get_selected(self):
		rs = []
		for i, c in enumerate(self.checkboxs):
			if c.GetValue(): 
				rs.append(self.chapter_urls[i])
		return rs

class ScrollTask(scrolled.ScrolledPanel):
	def __init__(self, parent, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize):
		scrolled.ScrolledPanel.__init__(self, parent, id, pos, size, style = wx.BORDER)
		self.SetBackgroundColour("white")
		self.sizer = wx.FlexGridSizer(rows = 1000, cols = 1, hgap = 0, vgap = 5)
		self.SetSizer(self.sizer)

	def add(self, panel_task):
		self.sizer.Add(panel_task, 1, wx.LEFT | wx.TOP, 5)
		self.sizer.Layout()
		length = self.sizer.GetItemCount() + 1
		width, height = panel_task.GetSize()
		self.SetScrollbars(1, 1, width + 2 * 5, height * length + 5 * (length - 1))

class PanelTask(wx.Panel):
	def __init__(self, parent, task, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize):
		wx.Panel.__init__(self, parent, id, pos, size)
		self.text_1 = wx.StaticText(self, -1, task.manga.name.decode("utf-8"), pos = (5, 5))
		self.text_2 = wx.StaticText(self, -1, u"", pos = (5, 25))
		self.gauge = wx.Gauge(self, -1, task.page_num, pos = (0, 45), size = (207, -1))
		self.gauge.SetValue(0)
		self.SetBackgroundColour("#66ccff")
		self.value = 0
		task.ui = self
		self.page_num = task.page_num
		rate = "%.1f" % (float(self.value) / self.page_num * 100)
		info = "%d / %d (%s%%)" % (self.value, self.page_num, rate)  
		self.text_2.SetLabel(info)

	def count(self):
		self.value += 1
		rate = "%.1f" % (float(self.value) / self.page_num * 100)
		info = "%d / %d (%s%%)" % (self.value, self.page_num, rate)  
		self.text_2.SetLabel(info)
		self.gauge.SetValue(self.value)

class PanelMain(wx.Panel):
	def __init__(self, parent, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize):
		wx.Panel.__init__(self, parent, id, pos, size)

		self.ctrl = wx.TextCtrl(self, -1, "", (10, 10), (280, -1))
		self.btn_1 = wx.Button(self, -1, u"链接", (300, 7), (-1, -1))
		self.chapter_scroll = ScrollChapter(self, -1, (237, 45), (150, 235))
		self.task_scroll = ScrollTask(self, -1, (10, 45), (220, 280))
		self.checkbox_1 = wx.CheckBox(self, -1, u"全选", (237, 290))
		self.checkbox_2 = wx.CheckBox(self, -1, u"反选", (237, 310))
		self.btn_2 = wx.Button(self, -1, u"下载", (287, 290), (100, 37))

		self.btn_1.Bind(wx.EVT_BUTTON, self.OnLink)
		self.checkbox_1.Bind(wx.EVT_CHECKBOX, self.OnSelectAll)
		self.checkbox_2.Bind(wx.EVT_CHECKBOX, self.OnSelectReverse)
		self.btn_2.Bind(wx.EVT_BUTTON, self.OnDownload)

		self.manga = None

	def OnSelectAll(self, evt):
		self.chapter_scroll.select_all(self.checkbox_1.GetValue())	

	def OnSelectReverse(self, evt):
		self.chapter_scroll.select_reverse()

	def OnLink(self, evt):
		self.manga = MH.Manga(self.ctrl.GetValue())
		if self.manga.parse():
			self.chapter_scroll.set_chapter(self.manga.chapter_url)
			self.checkbox_1.SetValue(False)
			self.checkbox_2.SetValue(False)
		else:
			dialog = wx.MessageDialog(self, u"URL格式错误，必须是漫画首页", u"提示", wx.OK | wx.ICON_INFORMATION)
			dialog.ShowModal()

	def OnDownload(self, evt):
		selection = self.chapter_scroll.get_selected()
		task = MH.Task(self.manga, selection, queue, queue2)
		if not task.parse():
			info = "《%s》下载过了，请转移同名文件夹以开始新的下载" % (self.manga.name)
			dialog = wx.MessageDialog(self, info.decode("utf-8"), u"提示", wx.OK | wx.ICON_INFORMATION)
			dialog.ShowModal()
			return
		panel_task = PanelTask(self.task_scroll, task)
		self.task_scroll.add(panel_task)
		task.run_task()

class FrameMain(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title, style = wx.CAPTION | wx.MINIMIZE_BOX | wx.CLOSE_BOX)

		self.panel = PanelMain(self)

		self.Show()
		self.Center()
		self.SetClientSize((395, 335))
		self.Fit()

def init_thread_pool():
	global queue, queue2
	queue = Queue.Queue(0)
	queue2 = Queue.Queue(0)
	map(lambda x : thread_pool.append(MH.Thread(queue, queue2, MH.handler_download)), xrange(NUM_THREAD))
	map(lambda x : x.setDaemon(True), thread_pool)
	map(lambda x : x.start(), thread_pool)

if __name__ == "__main__":
	app = App(False)
	app.MainLoop()
