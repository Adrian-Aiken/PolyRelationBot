#!/usr/bin/env python
"""
Telegram bot to graph relationships between people
"""
# Author: Adrian Aiken (adaiken@outlook.com)

import json
import logging
from telegram.ext import Updater, CommandHandler, Job
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import os
import pickle

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

    def __str__(self):
        return "[" + self.name1 + "] and [" + self.name2 + "] are [" + self.relationship + "]"

######################################################
###### Startup - needs to be present every time ######
######################################################
logger = logging.getLogger()
logger.setLevel(logging.INFO)

with open('config.json', 'r') as configfile:
    config = json.load(configfile)
with open('strings.json', 'r') as stringsfile:
    strings = json.load(stringsfile)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

nodes = set()

def saveNodes():
    f = file(config["nodes_file"], "w")
    pickle.dump(nodes, f)
    f.close()

if not os.path.exists(config["nodes_file"]):
    saveNodes()

f = open(config["nodes_file"], 'r+')
nodes = pickle.load(f)
f.close()

users = dict()
def addUser(handle, userId):
    users[handle.lower()] = userId;
    f = file(config["users_file"], "w");
    pickle.dump(users, f);
    f.close();

if not os.path.exists(config["users_file"]):
    addUser(u"Goatie", 103514643)
else:
    f = file(config["users_file"], "r+");
    users = pickle.load(f)
    f.close()

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

def removeFromGraph(name):
    toRemove = [n for n in nodes if n.hasName(name)]
    
    for node in toRemove:
        nodes.remove(node)

    saveNodes()

def purgeNodes():
    nodes.clear()
    saveNodes()

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
            if not nodeName.lower() in map(unicode.lower, visited):
                edges.append(node)
                toVisit.append(nodeName)

    return edges, visited

#######################
#### Graph Drawing ####
#######################
def generateGraph(name, bot):
    edges, nodes = getEdges(name)
    if len(edges) == 0:
        return False

    relations = dict()
    labels = dict()

    G = nx.Graph()
    G.clear()
    for edge in edges:
        G.add_edge(edge.name1.lower(), edge.name2.lower())
        relations[(edge.name1.lower(), edge.name2.lower())] = edge.relationship

    for node in nodes:
        if node[0] == '@' and node[1:].lower() in users:
            userId = users[node[1:].lower()]
            photos = bot.getUserProfilePhotos(userId, limit = 1)
            if len(photos.photos) > 0:
                photoId = photos.photos[0][0].file_id
                photoFile = bot.getFile(photoId)
                photoFile.download(node[1:])
                G.node[node.lower()]['image'] = mpimg.imread(node[1:]);
                img = mpimg.imread(node[1:])
        else:
            labels[node.lower()] = node
    
    plt.cla()

    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('auto')
    plt.axis('off')

    pos = nx.spring_layout(G)

    nx.draw_networkx_nodes(G, pos, node_size = 1400)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_edge_labels(G, pos, relations)
    nx.draw_networkx_labels(G, pos, labels)

    trans = ax.transData.transform
    trans2 = fig.transFigure.inverted().transform
   
    imgSize = config["imgSize"];
    i2 = imgSize/2.0
    for n in G:
        if 'image' in G.node[n]:
            xx,yy = ax.transData.transform(pos[n]) # figure coordinates
            xa,ya = fig.transFigure.inverted().transform((xx,yy)) # axes coordinates
            a = plt.axes([xa-i2,ya-i2, imgSize, imgSize])
            a.set_aspect('auto')
            a.imshow(G.node[n]['image'])
            plt.axis('off')  
            plt.title(n, y = -0.45)
    
    plt.savefig(config["graph_file"])
    plt.clf()

    return True

###############################################
#### Telegram message handling and parsing ####
###############################################
def isPrivate(update):
    return update.chat.type is 'private'

def addRelationship(bot, update):
    if not isPrivate(update):
        return;

    addUser(update.message.from_user.username, update.message.from_user.id);

    m = update.message.text.replace("/add ", "")

    if m.find(" + ") == -1:
        bot.sendMessage(update.message.chat_id, text = strings["error_add"])
        return

    name1 = m[:m.find(" + ")]
    if m.find(" = ") == -1:
        relationship = ""
        name2 = m[m.find(" + ") + 3:]
    else:
        relationship = m[m.find(" = ") + 3:]
        name2 = m[m.find(" + ") + 3:m.find(" = ")]
    
    if relationship.lower() in config["remove_words"]:
        removeRelationship(bot, update)
        return

    if name1.lower() in config["self_words"]:
        name1 = "@" + update.message.from_user.username
    if name2.lower() in config["self_words"]:
        name2 = "@" + update.message.from_user.username

    addNode(name1, name2, relationship)
    if relationship == "":
        relationship = "together"
    bot.sendMessage(update.message.chat_id, text = strings["added"].format(name1, name2, relationship))
        
def removeRelationship(bot, update):
    if not isPrivate(update):
        return;

    addUser(update.message.from_user.username, update.message.from_user.id);
    
    if update.message.text.find(", ") == -1:
        bot.sendMessage(update.message.chat_id, text = strings["error_remove"])
        return

    m = update.message.text.replace("/remove ", "").split(", ")
    name1 = m[0]
    name2 = m[1]

    if name1.lower() in config["self_words"]:
        name1 = "@" + update.message.from_user.username
    if name2.lower() in config["self_words"]:
        name2 = "@" + update.message.from_user.username

    removeNode(name1, name2)
    bot.sendMessage(update.message.chat_id, text = strings["removed"].format(name1, name2))

def showRelationship(bot, update):
    addUser(update.message.from_user.username, update.message.from_user.id);

    nameArray = update.message.text.split(' ', 1)
    name = ''

    if len(nameArray) == 1:
        name = "@" + update.message.from_user.username
    elif nameArray[1].strip().lower() in config["self_words"]:
        name = "@" + update.message.from_user.username
    else:
        name = nameArray[1].strip()

    if generateGraph(name, bot):
        photofile = open(config["graph_file"].encode("utf-8"), "rb")
        bot.sendPhoto(update.message.chat_id, photofile)
    else:
        bot.sendMessage(update.message.chat_id, text = strings["error_show"])

def showHelp(bot, update):
    addUser(update.message.from_user.username, update.message.from_user.id);
    bot.sendMessage(update.message.chat_id, text = strings["help"])

def removeAll(bot, update):
    if not isPrivate(update):
        return;

    name = update.message.text.replace("/removeAll", "").strip()
    if len(name) == 0:
        name = "@" + update.message.from_user.username
    elif name.lower() in config["self_words"]:
        name = "@" + update.message.from_user.username

    removeFromGraph(name)
    bot.sendMessage(update.message.chat_id, text = strings["remove_all"].format(name))

def purge(bot, update):
    if not isPrivate(update):
        return;

    if update.message.from_user.username.lower() in config["admins"]:
        purgeNodes()
        bot.sendMessage(update.message.chat_id, text = strings["purged"])

def register(bot, update):
    addUser(update.message.from_user.username, update.message.from_user.id);
    bot.sendMessage(update.message.chat_id, text = strings["registered"])

####################
#### Main stuff ####
####################
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    updater = Updater(config["bot_token"])
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("add", addRelationship))
    dp.add_handler(CommandHandler("remove", removeRelationship))
    dp.add_handler(CommandHandler("show", showRelationship, allow_edited = True))
    dp.add_handler(CommandHandler("help", showHelp))
    dp.add_handler(CommandHandler("removeAll", removeAll))
    dp.add_handler(CommandHandler("purge", purge))
    dp.add_handler(CommandHandler("register", register))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
