from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time, datetime
import numpy as np
from . import widgets_base as wb
import os.path as osp


class DataPlotterWidget(QtWidgets.QMainWindow):
    new_axes_created = QtCore.Signal()

    def __init__(self, dataplotter):
        super(DataPlotterWidget, self).__init__()
        self.setWindowTitle('DataPlotter')
        self.dlg = dataplotter #this dataplotter does not contain any channels yet

        self.graph = pg.GraphicsWindow()

        self.plot_item = self.graph.addPlot(title="DataPlotter", axisItems={
            'bottom': wb.TimeAxisItem(orientation='bottom')})

        self.plot_item.setLabels(bottom='time')

        self.plot_item.hideAxis('left')
        self.setCentralWidget(self.graph)

        self.axes = dict()
        self.update_axes()
        self.plot_item.vb.sigResized.connect(self.update_views)

        self._dock_tree = MyDockTreeWidget(dataplotter)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)

        self.show()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

    def remove_channel(self, channel):
        channel.widget.curve.setData([], [])
        return self.tree.remove_channel(channel)

    def set_green_days(self):
        self._dock_tree.mycontrolwidget.set_green_days()

    def update_axes(self):
        '''
        plots points at the beginning and the end of the selected plot, but does not connect them, to force the 
        plotItem to show the correct time interval. It would otherwise snap to [0,1]
        '''
        self.plot_item.clear()
        self.plot_item.plot( [self.dlg.earliest_point, self.dlg.earliest_point,
                                          self.dlg.latest_point, self.dlg.latest_point], [0, 0, 0, 0], connect='pairs')
        #first clears all axes from before
        for axis_name in self.axes.keys():
            self.axes[axis_name][0].scene().removeItem(self.axes[axis_name][1])
            print(axis_name + ' removed')
        #self.plot_item.clear() #clear does not destroy AxisItems
        self.axes = dict()
        print(self.dlg.axis_types_list)
        iterno = 0
        for axis_name in self.dlg.axis_types_list:
            if axis_name not in self.axes:
                '''
                if iterno%2:
                    place = "right"
                else:
                    place = "left"
                '''
                self.axes[axis_name] = {0:pg.ViewBox(), 1:pg.AxisItem("left")}
                view_box = self.axes[axis_name][0]
                axis_item = self.axes[axis_name][1]

                self.plot_item.layout.addItem(axis_item, 2, 2*iterno) #second index influences vertical length, third index influences horizontal position
                self.plot_item.scene().addItem(view_box)
                axis_item.linkToView(view_box)
                view_box.setXLink(self.plot_item)
                #view_box.setZValue(0)
                axis_item.setLabel(axis_name, color='#ff0000')
                iterno += 1
                print(axis_name + ' added')
        self.update_views()

    def update_views(self):
        for axis_name in self.axes:
            view_box = self.axes[axis_name][0]
            view_box.setGeometry(self.plot_item.vb.sceneBoundingRect())
            view_box.linkedViewChanged(self.plot_item.vb, view_box.XAxis)

    def add_to_axis(self, plotter_item):
        self.axes[plotter_item.channel.axis_type][0].addItem(plotter_item.curve)
        pass

    def remove_from_axis(self, plotter_item):
        self.axes[plotter_item.channel.axis_type][0].removeItem(plotter_item.curve)
        pass


class PlotterItem(wb.MyTreeItem):

    def initialize(self, channel):
        self.channel = channel

        self.curve = pg.PlotDataItem(pen=pg.mkPen(color=self.channel.color))
        self.plot_points(channel.values, channel.times)

        self.button = QtWidgets.QPushButton(channel.name)
        self.button.clicked.connect(self.ask_color)
        self.dlg.widget.tree.setItemWidget(self, 0, self.button)

        self.axischoice = QtWidgets.QComboBox()
        self.axischoice.addItems(self.dlg.axis_types_list)
        self.new_axis_text = "New Axis..."
        self.axischoice.addItem(self.new_axis_text)
        self.axischoice.setCurrentIndex(self.axischoice.findText(self.channel.axis_type))
        self.axischoice.currentIndexChanged.connect(self.update_axes)
        self.dlg.widget.tree.setItemWidget(self, 2, self.axischoice)

        self.set_color(self.channel.color)
        self.dlg.widget.new_axes_created.connect(self.update_combo_box)

    def ask_color(self):
        color = QtGui.QColor()
        color.setNamedColor(self.channel.color)
        color = QtWidgets.QColorDialog.getColor(color)
        self.channel.color = color.name()

    def plot_points(self, vals, times):
        time_span = (times > self.channel.parent.earliest_point) * (times < self.channel.parent.latest_point)

        self.values = [val for val in vals[time_span]]
        self.times = [time for time in times[time_span]]
        if self.channel.visible:
            data = {'x':self.times, 'y':self.values} #required format for setData of a PlotDataItem
            self.curve.setData(data)

            self.dlg.widget.axes[self.channel.axis_type][0].addItem(self.curve)
            self.dlg.widget.update_axes()

        self.curve.setVisible(self.channel.visible)

    def set_color(self, color):
        self.button.setStyleSheet('background-color: ' + color)
        qt_color = QtGui.QColor()
        qt_color.setNamedColor(color)
        self.curve.setPen(pg.mkPen(qt_color))

    def get_axis_type_index(self, channel):
        return self.dlg.axis_types_list.index(channel.axis_type)

    def update_axes(self, index):
        choice = str(self.axischoice.currentText())
        self.dlg.widget.remove_from_axis(self)
        if choice == self.new_axis_text:
            new_name = self.make_new_axis()
            if new_name is not None:
                self.channel.axis_type = new_name
                self.dlg.widget.new_axes_created.emit()
                #self.axischoice.insertItem(len(self.dlg.axis_types_list), self.channel.axis_type)
        else:
            self.channel.axis_type = choice

        self.dlg.widget.update_axes()
        self.dlg.widget.add_to_axis(self)

        #self.update_combo_box()

    def update_combo_box(self):
        #updates the comboboxes of all the channels
        for chan in self.dlg.channels.values():
            combo = chan.widget.axischoice
            combo.blockSignals(True)
            for i in range (0, combo.count()):
                combo.removeItem(0)
            combo.addItems(self.dlg.axis_types_list)
            combo.addItem(self.new_axis_text)
            combo.setCurrentIndex(combo.findText(chan.axis_type))
            combo.blockSignals(False)

    def make_new_axis(self):
        new_name, ok = QtWidgets.QInputDialog.getText(None, "New Axis Name:", "NewAxis", QtWidgets.QLineEdit.Normal, "")
        if ok and new_name is not '':
            self.channel.parent.axis_types_list.append(new_name)
            return new_name
        else:
            return None


class PlotterTree(wb.MyTreeWidget):
    item_class = PlotterItem

    def __init__(self, dataplotter):
        super(wb.MyTreeWidget, self).__init__()
        labels = ["Channel", "Visible", "Axis Type"]
        self.setHeaderLabels(labels)
        self.setColumnCount( len(labels) )
        self.dlg = dataplotter
        self.itemChanged.connect(self.update)
        self.setSortingEnabled(True)

    def update(self):
        for channel in self.dlg.channels.values():
            channel.visible = channel.widget.checkState(1) == 2
            #channel.axis_type =


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

    def remove_channel(self, channel):
        return self.tree.remove_channel(channel)


class MyDockTreeWidget(QtWidgets.QDockWidget):
    def __init__(self, dataplotter):
        super(MyDockTreeWidget, self).__init__()
        self.mycontrolwidget = MyControlWidget(dataplotter)
        self.tree = self.mycontrolwidget.tree
        self.setWidget(self.mycontrolwidget)

