"""***************************************************************************
**
** Copyright (C) 2005-2005 Trolltech AS. All rights reserved.
**
** This file is part of the example classes of the Qt Toolkit.
**
** This file may be used under the terms of the GNU General Public
** License version 2.0 as published by the Free Software Foundation
** and appearing in the file LICENSE.GPL included in the packaging of
** this file.  Please review the following information to ensure GNU
** General Public Licensing requirements will be met:
** http://www.trolltech.com/products/qt/opensource.html
**
** If you are unsure which license is appropriate for your use, please
** review the following information:
** http://www.trolltech.com/products/qt/licensing.html or contact the
** sales department at sales@trolltech.com.
**
** This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
** WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
**
***************************************************************************"""

import sys
from PyQt4 import QtCore, QtGui, QtXml



def getPath(node):
    path = ''
    if not node.parentNode().isNull() and node.parentNode().nodeType() != QtXml.QDomNode.DocumentNode:
        path = getPath(node.parentNode()) + " -> "
    return path + node.nodeName()

class DomItem:
    def __init__(self, node, row, parent=None):
        self.domNode = node
        # Record the item's location within its parent.
        self.rowNumber = row
        self.parentItem = parent
        self.childItems = {}

        self.editable = False
        if self.domNode.nodeType() == QtXml.QDomNode.ElementNode:
            self.editable = (self.domNode.childNodes().count() == 1 and self.domNode.childNodes().at(0).nodeType() == QtXml.QDomNode.TextNode) or (not self.domNode.hasChildNodes())


    def node(self):
        return self.domNode

    def parent(self):
        return self.parentItem

    def child(self, i):
        if self.childItems.has_key(i):
            return self.childItems[i]

        if i >= 0 and i < self.domNode.childNodes().count():
            childNode = self.domNode.childNodes().item(i)
            childItem = DomItem(childNode, i, self)
            self.childItems[i] = childItem
            return childItem

        return 0

    def row(self):
        return self.rowNumber


    #-------additional 

    #editable flag. Need to remove #text nodes and organize editable control
    def isEditable(self):
        return self.editable

    #child counts. Need to remove #text nodes
    def childCount(self):
        if self.editable:
            return 0
        else:
            return self.domNode.childNodes().count()

    #item value. Need to remove #text nodes
    def itemValue(self):
        if self.editable:
            return self.domNode.childNodes().at(0).nodeValue()
        else:
            return self.domNode.nodeValue()

    #set item value. Need to remove #text nodes
    def setItemValue(self, value):
        if self.editable:
            if not self.domNode.hasChildNodes():
                #create text node
                textNode = self.domNode.ownerDocument().createTextNode(value)
                self.domNode.appendChild(textNode)
            else:
                self.domNode.childNodes().at(0).setNodeValue(value)



    def getNodePath(self):
        return getPath(self.domNode)




class DomModel(QtCore.QAbstractItemModel):
    def __init__(self, document, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        self.domDocument = document
        self.rootItem = DomItem(self.domDocument, 0)

    def columnCount(self, parent):
        return 3

    #get editable flag by index
    def isEditable(self, index):
        if not index.isValid():
            return QtCore.QVariant()

        item = index.internalPointer()

        return item.isEditable()

    def nodePath(self, index):
        if not index.isValid():
            return QtCore.QVariant()

        item = index.internalPointer()

        return item.getNodePath()



    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        item = index.internalPointer()

        node = item.node()
        attributes = QtCore.QStringList()
        attributeMap = node.attributes()

        if index.column() == 0:
            return QtCore.QVariant(node.nodeName())

        elif index.column() == 1:
            for i in range(0, attributeMap.count()):
                attribute = attributeMap.item(i)
                attributes.append(attribute.nodeName() + "=\"" + \
                                  attribute.nodeValue() + "\"")

            return QtCore.QVariant(attributes.join(" "))
        elif index.column() == 2:
            #return QtCore.QVariant(node.nodeValue().split("\n").join(" "))
            return QtCore.QVariant(item.itemValue().split("\n").join(" "))

        else:
            return QtCore.QVariant()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            item = index.internalPointer()
            node = item.node()
            item.setItemValue(value)

            self.emit(QtCore.SIGNAL('dataChanged(const QModelIndex &,const QModelIndex &)'), index, index)
            return node
        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        item = index.internalPointer()
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return QtCore.QVariant(self.tr("Name"))
            elif section == 1:
                return QtCore.QVariant(self.tr("Attributes"))
            elif section == 2:
                return QtCore.QVariant(self.tr("Value"))
            else:
                return QtCore.QVariant()

        return QtCore.QVariant()

    def index(self, row, column, parent):
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, child):
        if not child.isValid():
            return QtCore.QModelIndex()

        childItem = child.internalPointer()
        parentItem = childItem.parent()

        if not parentItem or parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()
