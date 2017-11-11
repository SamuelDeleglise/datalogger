from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time, datetime
import numpy as np
from . import widgets_base as wb
import os.path as osp


class DataPlotterWidget(QtWidgets.QMainWindow):
    def __init__(self, dataplotter):
        super(DataPlotterWidget, self).__init__()
        self.dlg = dataplotter #this dataplotter does not contain any channels yet

        self.graph = pg.GraphicsWindow(title="DataPlotter")
        self.plot_item = self.graph.addPlot(title="DataPlotter", axisItems={
            'bottom': wb.TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)

        self._dock_tree = MyDockTreeWidget(dataplotter)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)

        self.show()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

class PlotterItem(wb.MyTreeItem):
    COLORS = ['red', 'green', 'blue', 'cyan', 'magenta']
    N_CHANNELS = 0

    def initialize(self, channel):
        color = self.COLORS[self.N_CHANNELS % len(self.COLORS)]
        self.setBackground(0, QtGui.QColor(color))
        self.channel = channel

        self.curve = self.dlg.widget.plot_item.plot(pen=color[0])
        self.plot_points(self.channel.values, self.channel.times)

        PlotterItem.N_CHANNELS += 1

    def plot_points(self, vals, times):
        time_span = (times > self.channel.parent.earliest_point) * (times < self.channel.parent.latest_point)

        self.values = [val for val in vals[time_span]]
        self.times = [time for time in times[time_span]]

        if self.channel.visible:
            self.curve.setData(self.times, self.values)
        self.curve.setVisible(self.channel.visible)

class PlotterTree(wb.MyTreeWidget):
    item_class = PlotterItem

    def __init__(self, dataplotter):
        super(wb.MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Channel", "Visible"])
        self.setColumnCount(2)
        self.dlg = dataplotter
        self.itemChanged.connect(self.update)
        self.setSortingEnabled(True)

    def update(self):
        for channel in self.dlg.channels.values():
            channel.visible = channel.widget.checkState(1) == 2


class MyControlWidget(QtWidgets.QWidget):
    SELECTED_GREEN_COLOR = 'darkGreen'
    SELECTED_GREEN_FONT = QtGui.QTextCharFormat()
    SELECTED_GREEN_FONT.setBackground(QtGui.QColor(SELECTED_GREEN_COLOR))

    GREEN_COLOR = 'green'
    GREEN_FONT = QtGui.QTextCharFormat()
    GREEN_FONT.setBackground(QtGui.QColor(GREEN_COLOR))

    SELECTED_BLANK_COLOR = 'grey'
    SELECTED_BLANK_FONT = QtGui.QTextCharFormat()
    SELECTED_BLANK_FONT.setBackground(QtGui.QColor(SELECTED_BLANK_COLOR))

    BLANK_FONT = QtGui.QTextCharFormat()
    BLANK_FONT.setBackground(QtGui.QColor('white'))

    def __init__(self, dataplotter):
        super(MyControlWidget, self).__init__()
        self.dlg = dataplotter
        self.lay_v = QtWidgets.QVBoxLayout()
        self.setLayout(self.lay_v)
        self.lay_h = QtWidgets.QHBoxLayout()

        self.real_time_button = QtWidgets.QRadioButton('real-time')
        self.calendar_button = QtWidgets.QRadioButton('choose date')

        self.lay_radio = QtWidgets.QVBoxLayout()
        for widget in [self.real_time_button, self.calendar_button]:
            self.lay_radio.addWidget(widget)
        self.lay_h.addLayout(self.lay_radio)

        self.label = QtWidgets.QLabel("Show ")
        self.lay_h.addWidget(self.label)
        self.spinbox_days = QtWidgets.QSpinBox()
        self.lay_h.addWidget(self.spinbox_days)
        self.label_day = QtWidgets.QLabel("days, ")
        self.lay_h.addWidget(self.label_day)
        self.spinbox_hours = QtWidgets.QSpinBox()
        self.label_hours = QtWidgets.QLabel("hours, ")
        self.lay_h.addWidget(self.spinbox_hours)
        self.lay_h.addWidget(self.label_hours)
        self.spinbox_minutes = QtWidgets.QSpinBox()
        self.label_minutes = QtWidgets.QLabel("minutes")
        self.lay_h.addWidget(self.spinbox_minutes)
        self.lay_h.addWidget(self.label_minutes)
        self.lay_h.addStretch()

        self.tree = PlotterTree(self.dlg)
        self.lay_v.addWidget(self.tree)

        self.lay_v.addLayout(self.lay_h)
        self.spinbox_days.setValue(self.dlg.days_to_show)
        self.spinbox_hours.setValue(self.dlg.hours_to_show)
        self.spinbox_minutes.setValue(self.dlg.minutes_to_show)

        self.real_time_button.setChecked(self.dlg.show_real_time)
        self.calendar_button.setChecked(not self.dlg.show_real_time)
        self.calendar = QtWidgets.QCalendarWidget()
        self.calendar.setSelectedDate(self.dlg.selected_date)
        self.calendar.setEnabled(not self.dlg.show_real_time)
        self.lay_v.addWidget(self.calendar)

        self.real_time_button.clicked.connect(self.real_time_toggled)
        self.calendar_button.clicked.connect(self.real_time_toggled)
        self.calendar.selectionChanged.connect(self.real_time_toggled)

        self.spinbox_days.valueChanged.connect(self.update_days_to_show)
        self.spinbox_hours.valueChanged.connect(self.update_hours_to_show)
        self.spinbox_minutes.valueChanged.connect(self.update_minutes_to_show)

        self.selected_list = [self.dlg.selected_date - datetime.timedelta(n) for n in range(self.dlg.days_to_show)]

        self.set_green_days()
        self.update_calendar_display()

    def set_green_days(self):
        """
        Days with existing data are green in the calendar
        """
        font = QtGui.QTextCharFormat()
        font.setBackground(QtGui.QColor(self.GREEN_COLOR))
        for day in self.dlg.find_all_dates():
            self.calendar.setDateTextFormat(day, font)

    def real_time_toggled(self):
        real_time =  self.real_time_button.isChecked()
        self.dlg.show_real_time = real_time
        self.calendar.setEnabled(not real_time)
        self.update_calendar_display()

        if not real_time:
            date = self.calendar.selectedDate()
        else:
            date = QtCore.QDate.currentDate()

        for widget in [self.spinbox_hours, self.label_hours, self.spinbox_minutes, self.label_minutes]:
            widget.setVisible(real_time)
        self.spinbox_days.setMinimum(0 if real_time else 1)
        self.dlg.selected_date = date.toPyDate()
        self.update_calendar_display()

    def update_calendar_display(self):
        selection_color = self.SELECTED_GREEN_COLOR if self.dlg.selected_date in self.dlg.all_dates else self.SELECTED_BLANK_COLOR
        self.calendar.setStyleSheet("QTableView{selection-background-color: %s}"%selection_color)
        for date in self.selected_list:
            self.calendar.setDateTextFormat(date, self.GREEN_FONT if date in self.dlg.all_dates else self.BLANK_FONT)
        self.selected_list = [self.dlg.selected_date - datetime.timedelta(n) for n in range(self.dlg.days_to_show)]
        for date in self.selected_list:
            self.calendar.setDateTextFormat(date, self.SELECTED_GREEN_FONT if date in self.dlg.all_dates else self.SELECTED_BLANK_FONT)

    def update_days_to_show(self):
        days = self.spinbox_days.value()
        self.dlg.days_to_show = days
        self.update_calendar_display()

    def update_hours_to_show(self):
        hours = self.spinbox_hours.value()
        self.dlg.hours_to_show = hours
        self.update_calendar_display()

    def update_minutes_to_show(self):
        minutes = self.spinbox_minutes.value()
        self.dlg.minutes_to_show = minutes
        self.update_calendar_display()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)


class MyDockTreeWidget(QtWidgets.QDockWidget):
    def __init__(self, dataplotter):
        super(MyDockTreeWidget, self).__init__()
        self.mycontrolwidget = MyControlWidget(dataplotter)
        self.tree = self.mycontrolwidget.tree
        self.setWidget(self.mycontrolwidget)
