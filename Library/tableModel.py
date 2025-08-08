from PyQt5.QtCore import QVariant, Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtWidgets import QApplication, QTableView, QVBoxLayout, QWidget, QMessageBox
from scipy.interpolate import interp1d

from Library.dataMager import Calculator
from PyQt5.Qt import QFont, QColor
from numpy import linspace,random,sin, exp, where, zeros, argmax,append, log,exp, arange,diff,ones,split,argsort,array, insert, append, delete,nan
from PyQt5.QtCore import QTimer


class MyTableModel(QAbstractTableModel):
    def __init__(self, calc: Calculator, parent=None,index=None):
        super().__init__()
        self.tabIndex = index
        self.sort_column = None
        self.calc = calc
        self.parent = parent
        self.data = self.calc.wiggledata
        self.sortind = arange(len(self.data['year']))
        self.formats = {'year': ['%i',1], 'fm': ['%.4f',1], 'fm_sig': ['%.4f',1], 'age': ['%i',1], 'age_sig': ['%i',1], 'active': ['',1],
                        'A_i': ['%.2f',1],'label':['%s',1],'range':['%i',1]}
        self.Headerformats = {'year': 'Year', 'fm': 'F¹⁴C', 'fm_sig': 'ΔF¹⁴C', 'age':'¹⁴C age','age_sig': 'Δ¹⁴C age', 'active': '',
                        'A_i': 'A_i','label':'Label','range':'Integration range'}
        self.updateHeader()


    def rowCount(self, parent=None):
        try:
            return len(self.data[next(iter(self.data))])
        except:
            return 0

    def columnCount(self, parent=None):
        return len(self.columns)
        # return len(self.data)  # One column for keys, one for values

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = self.sortind[index.row()]
        activated = self.data['active'][row]
        key = self.columns[column]
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole,Qt.EditRole):
            if key == 'active':
                return ''
            if self.formats[key][1] != 1:
                return self.formats[key][0] % (self.data[key][row]*self.formats[key][1])
            else:
                return self.formats[key][0] % (self.data[key][row])
        elif role == Qt.CheckStateRole:
            if key == 'active':
                if activated:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
        elif role == Qt.BackgroundColorRole:
            if not activated:
                bgColor = QColor(100, 100, 100)
                bgColor.setAlpha(140)
                return QVariant(bgColor)
        elif role == 1:
            return self.data[key][row]
        else:
            return None

    def setData(self, index, value, role=Qt.EditRole,recalc=True):
        if role == Qt.EditRole and index.isValid():
            column = index.column()
            row = self.sortind[index.row()]
            key = self.columns[column]
            self.fmcalc = False
            breakflag = False
            if key in ['year', 'fm', 'fm_sig', 'bp', 'age', 'age_sig','range']:
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                    if key  == 'range':
                        value = int(value)
                        if value < 1:
                            value = 1
                    self.data[key][row] = value
                    self.fmcalc = False
                    if key == 'fm' or key  == 'fm_sig':
                        self.fmcalc = False
                    elif key == 'age' or key == 'age_sig':
                        self.fmcalc = True
                except ValueError:
                    breakflag = True
                    print(value)
            if key in ['label']:
                try:
                    self.data[key][row] = value
                except ValueError:
                    self.data[key] = array(self.data[key],dtype=str)
                    self.data[key][row] = value
            if breakflag:
                QMessageBox.warning(None, "Invalid Input", "Please enter a valid number.")
                return False
            if recalc:
                self.calc.recalc_wiggledata(fm = self.fmcalc)
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                self.parent.recalcFlag = True
                self.parent.recalcIndex = self.tabIndex
                self.parent.redraw()
                return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.Headerformats[self.columns[section]]  # Column headers
        elif orientation == Qt.Vertical:
            return str(section)  # Row index

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        column = index.column()
        key = self.columns[column]
        if key != 'active' and 'A_i' not in key:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable  # Make values editable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled  # Keys remain read-only

    def updateHeader(self):
        self.beginResetModel()
        self.columns = []
        if 'label' in self.calc.wiggledata:
            self.columns += ['label']
        if self.parent.ageBox.isChecked():
            self.columns += ['year', 'age', 'age_sig', 'active']#,'range'
        else:
            self.columns += ['year', 'fm', 'fm_sig', 'active']#,'range'
        for curve in self.calc.curves:
            if curve is not None:
                key = f'{curve}A_i'
                self.columns.append(key)
                self.formats[key] = ['%.2f %%',100]
                self.Headerformats[key] = f'Agreement\n{curve}'
        self.endResetModel()
        
        # Add this line to adjust scroll area width after model update
        QTimer.singleShot(0, self.parent.adjust_scrollarea_width)

    def insertRows(self, position, rows=1, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for row in range(rows):
            for key in self.data.keys():
                if key == 'active':
                    self.data[key] = insert(self.data[key],row,True)
                else:
                   self.data[key] = insert(self.data[key],row,self.data[key][-1])
            self.sortind =  insert(self.sortind,row,row)
        self.endInsertRows()
        return True


    def tableClicked(self, item):
        col = item.column()
        row = self.sortind[item.row()]
        colkey = self.columns[col]
        if colkey == 'active':
            if item.data(role=Qt.CheckStateRole) == Qt.Checked:
                self.data['active'][row] = False
            else:
                self.data['active'][row] = True
            self.calc.recalc_wiggledata()
            self.parent.recalcFlag = True
            self.parent.recalcIndex = self.tabIndex
            self.parent.redraw()

    def addDate(self):
        data = self.calc.curveData.data
        self.beginResetModel()
        deltat = 1
        key = 'ETHCal'
        syntherr = 1.5 / 1000
        curve = interp1d(data[key]['calendaryear'],data[key]['fm'],fill_value=nan)
        curve_sig = interp1d(data[key]['calendaryear'],data[key]['fm_sig'],fill_value=nan)
        try:
            year = self.calc.wiggledata['year'][-1]+deltat
        except:
            year = 1800
        val1 = random.normal(curve(year), curve_sig(year))
        self.calc.wiggledata['year'] = append(self.calc.wiggledata['year'], year)
        self.calc.wiggledata['fm'] = append(self.calc.wiggledata['fm'], val1)
        self.calc.wiggledata['fm_sig'] = append(self.calc.wiggledata['fm_sig'], val1*syntherr)
        self.calc.wiggledata['range'] = append(self.calc.wiggledata['range'], 1)
        self.calc.wiggledata['active'] = append(self.calc.wiggledata['active'], True)
        for key in self.calc.wiggledata:
            if key not in ['year','fm','fm_sig','age','age_sig','active','range']:
                self.calc.wiggledata[key] = append(self.calc.wiggledata[key],'')
        self.calc.recalc_wiggledata(fm=False)
        self.calc.recalc_all()
        #self.parent.recalcFlag = True
        self.parent.redraw()
        if len(self.sortind) != len(self.data['year']):
            self.sort(self.sort_column,self.order)
        self.endResetModel()
        # Add this line to adjust scroll area width after adding data
        QTimer.singleShot(0, self.parent.adjust_scrollarea_width)

    def removeRows(self, row, count=1, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        rowind = self.sortind[row]
        for key in self.data.keys():
            self.data[key] = delete(self.data[key],rowind)
        self.calc.wiggledata = self.data
        self.sort(self.sort_column,self.order)
        self.parent.recalcFlag = True
        self.parent.ecalcIndex = self.parent.tabWidget.currentIndex()
        self.endRemoveRows()

        # Add this line to adjust scroll area width after removing rows
        QTimer.singleShot(0, self.parent.adjust_scrollarea_width)
        
        return True

    def sort(self, column, order):
        self.sort_column =  column
        self.order = order
        if column == -1:
            self.sortind = arange(len(self.data['year']))
        key = self.columns[column]
        self.layoutAboutToBeChanged.emit()
        self.sortind = argsort(self.data[key])

        if order == Qt.DescendingOrder:
            self.sortind = self.sortind[::-1]
        self.layoutChanged.emit()

