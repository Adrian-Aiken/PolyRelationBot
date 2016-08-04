#!/usr/bin/env python
"""
Telegram bot to graph relationships between people
"""
# Author: Adrian Aiken (adaiken@outlook.com)

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pickle
import os

NODES_FILE_NAME = "nodes.pkl";
nodes = set()

class RelationNode:
    def __init__(self, name1, name2, relationship):
        names = [name1, name2]
        names.sort()

        self.name1 = names[0]
        self.name2 = names[1]
        self.relationship = relationship

    def equals(self, other):
        if (self.name1.lower() == other.name1.lower()) or (self.name1.lower() == other.name2.lower()):
            if (self.name2.lower() == other.name1.lower()) or (self.name2.lower() == other.name2.lower()):
                return True
        return False

    def hasName(self, name):
        return name.lower() == self.name1.lower() or name.lower() == self.name2.lower()

    def getOtherName(self, name):
        if name.lower() == self.name1.lower():
            return self.name2
        return self.name1

######################################################
###### Startup - needs to be present every time ######
######################################################
if not os.path.exists(NODES_FILE_NAME):
    saveNodes()

f = file(NODES_FILE_NAME)
nodes = pickle.load(f)

###########################
#### Graph Managemenet ####
###########################
def addNode(name1, name2, relationship):
    newNode = RelationNode(name1, name2, relationship)
    oldNode = next((x for x in nodes if newNode.equals(x)), None)

    if oldNode is not None:
        nodes.remove(oldNode)

    nodes.add(newNode)
    saveNodes()

def removeNode(name1, name2):
    newNode = RelationNode(name1, name2, "")
    oldNode = next((x for x in nodes if newNode.equals(x)), None)

    if oldNode is not None:
        nodes.remove(oldNode)

    saveNodes()

def saveNodes():
    f = file(NODES_FILE_NAME, "w")
    pickle.dump(nodes, f)
    f.close()

def getEdges(name):
    visited = []
    toVisit = [name]
    edges = []

    while len(toVisit) is not 0:
        curName = toVisit.pop()
        visited.append(curName)

        curNodes = [n for n in nodes if n.hasName(curName)]
        for node in curNodes:
            nodeName = node.getOtherName(curName)
            if not nodeName.lower() in map(str.lower, visited):
                edges.append(node)
                toVisit.append(nodeName)

    return edges, visited

#######################
#### Graph Drawing ####
#######################
def generateGraph(name):
    edges, nodes = getEdges(name)


def main():
    getEdges("bob")    

if __name__ == '__main__':
    main()