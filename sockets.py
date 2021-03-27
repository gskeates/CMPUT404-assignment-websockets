#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Copyright (c) 2021 Graeme Keates
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, redirect, request
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()

    def add_set_listener(self, listener):
        self.listeners.append(listener)

    def remove(self, listener):
        self.listeners.remove(listener)

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners(entity)

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners(entity)

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity, dict())

    def world(self):
        return self.space

myWorld = World()

def set_listener( entity, data ):
    ''' do something with the update ! '''


myWorld.add_set_listener(set_listener)

@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return redirect('/static/index.html', code=302)

def read_ws(ws, client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME

    # Read messages from client
    try:
        while True:
            msg = ws.receive()
            print("WS RECV: ", msg)
            if msg is not None:
                packet = json.loads(msg)

                # Add to listeners bucket
                # send_all_json( packet )
            else:
                break
    except:
        '''Done'''

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME

    # Create new client

    # Spawn thread to read messages
    g = gevent.spawn(read_ws, ws, set_listener)

    # Block for updates from client
    try:
        while True:
            # Get update to world, send back to client
            pass
            # msg = myWorld.get()
            # print(msg)
            # ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print("WS Error ", e)
    finally:
        myWorld.remove(listener)
        gevent.kill(g)


# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    input_json = flask_post_json()
    if 'body' in input_json.keys():
        data = input_json['body']
    else:
        data = input_json

    if request.method == 'PUT':
        # Set
        myWorld.set(entity, data)

    elif request.method == 'POST':
        # Update
        for key, value in data.items():
            myWorld.update(entity, key, value)

    e = myWorld.get(entity)
    return flask.jsonify(e)

@app.route("/world", methods=['POST','GET'])
def world():
    '''you should probably return the world here'''
    if request.method == 'POST':
        data = flask_post_json()
        myWorld.set_world(data)

    return myWorld.world()

@app.route("/entity/<entity>")
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    e = myWorld.get(entity)
    return flask.jsonify(e)


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    return myWorld.world()



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
