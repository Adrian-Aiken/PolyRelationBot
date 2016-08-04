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
    relations = dict()
    labels = dict()

    G = nx.Graph()
    G.clear()
    for edge in edges:
        G.add_edge(edge.name1.lower(), edge.name2.lower())
        relations[(edge.name1.lower(), edge.name2.lower())] = edge.relationship

    for node in nodes:
        labels[node.lower()] = node

    pos = nx.spring_layout(G)

    plt.cla()
    plt.axis('off')
    nx.draw_networkx_nodes(G, pos, node_size = 700)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_edge_labels(G, pos, relations)
    nx.draw_networkx_labels(G, pos, labels)

    plt.savefig("save.png")

def main():
    generateGraph("Jay")

if __name__ == '__main__':
    main()

'''
img=mpimg.imread('bunwolf.jpg')
# draw graph without images
G =nx.Graph()
G.add_edge('a','b',image=img,size=0.1)
G.add_edge('b','c',image=img,size=0.05)
G.add_edge('c','d',image=img,size=0.02)
G.add_edge('d','e',image=img,size=0.075)
G.add_edge('a','a',image=img,size=0.2)

pos=nx.spring_layout(G)
nx.draw(G,pos)

# add images on edges
ax=plt.gca()
fig=plt.gcf()
label_pos = 0.5 # middle of edge, halfway between nodes
trans = ax.transData.transform
trans2 = fig.transFigure.inverted().transform
imsize = 0.1 # this is the image size
for (n1,n2) in G.edges():
    (x1,y1) = pos[n1]
    (x2,y2) = pos[n2]
    (x,y) = (x1 * label_pos + x2 * (1.0 - label_pos),
             y1 * label_pos + y2 * (1.0 - label_pos))
    xx,yy = trans((x,y)) # figure coordinates
    xa,ya = trans2((xx,yy)) # axes coordinates
    imsize = G[n1][n2]['size']
    img =  G[n1][n2]['image']
    a = plt.axes([xa-imsize/2.0,ya-imsize/2.0, imsize, imsize ])
    a.imshow(img)
    a.set_aspect('equal')
    a.axis('off')
plt.savefig('save.png') 
'''