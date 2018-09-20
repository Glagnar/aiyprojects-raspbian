#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import requests
import json
import time
import re

import aiy.assistant.grpc
import aiy.audio
import aiy.voicehat

# Added by Thomas
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)

def send_request(nick_name, project):
    try:
        print("Trying to reach: https://devices.alexandra.dk/webUI/sensors/nick/" + nick_name + "/" + project + ".json")
        response = requests.get(
            url="https://devices.alexandra.dk/webUI/sensors/nick/" + nick_name + "/" + project + ".json",
            headers={
                "Authorization": "Basic c3BlYWtVc2VyOkxpdHRsZUJpdGNoOTM=",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
        parsed_json = response.json()
        if len(parsed_json['sensorNames']) > 0:
            return parsed_json['sensorNames'][0]
        else:
            return None
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

def send_message(nick_name, project, action):
    deviceId = send_request(nick_name, project)
    if deviceId is None:
        return False

    current_time = int(round(time.time() * 1000))
    payload = '{"type":"command", "values":{"action":"'+action+'", "target":"'+deviceId+'"}, "sensorId":"", "time":'+str(current_time)+'}'
    client = mqtt.Client("LOCALCONNECTION") #create new instance
    client.connect("localhost") #connect to broker
    client.publish("/iot/commands/aiy/" + deviceId, payload)#publish$
    print('I have send a message:\t /iot/commands/aiy/' + deviceId + ' - ' + action)
    return True

def main():
    status_ui = aiy.voicehat.get_status_ui()
    status_ui.status('starting')
    assistant = aiy.assistant.grpc.get_assistant()
    button = aiy.voicehat.get_button()

    project = ''
    action = ''
    nick_name = ''
    running = True
    with aiy.audio.get_recorder():
        while running:
            status_ui.status('ready')
            print('Press the button and speak')
            print('Commands:\n"give status"\n"set project <projectname>"\n"clear project"\n"tell <devicename> to <action>"\n"clear command"\n"send message"')
            button.wait_for_press()
            status_ui.status('listening')
            print('Listening...')
            text, audio = assistant.recognize()
            if text:
                print('You said "', text, '"')
            if audio:
                print('You said "', text, '"')
                if text[:11] == 'set project':
                    project = text[11:]
                    project = project.replace(" ","")
                    aiy.audio.say('Project set ' + text[11:])
                    print('Project set to '+project)
                elif text[:13] == 'clear project':
                    project = ''
                    aiy.audio.say('Project cleared')
                    print('Project cleared')
                elif text[:13] == 'clear command':
                    nick_name = ''
                    action = ''
                    aiy.audio.say('Command cleared')
                    print('Command cleared')
                elif text[:11] == 'give status':
                    print('Project set to: \t'+project+'\nDevice set to:\t'+nick_name+'\nCommand set to:\t'+action);
                elif text[:4] == 'tell' and project != '':
                    # Splits the text at the key words: command, at & do.
                    # commandData[1] = sensor nick_name
                    # commandData[2] = action
                    commandData = re.split('tell\s|\sto\s',text)
                    print(commandData)
                    action = commandData[2]
                    nick_name = commandData[1]

                    aiy.audio.say('Command received: ' + commandData[2] + " " + commandData[1])
                elif text[:12] == 'send message':
                    if project != '' and nick_name != '' and action != '':
                        if send_message(commandData[1], project, commandData[2]):
                            aiy.audio.say('Message send')
                        else:
                            print('Sending message failed. No device ('+nick_name+') in project '+project+'.')
                            aiy.audio.say('Sending message failed. No device with that id.')
                    else:
                        print('You need to set a project and tell the device what to do before you can send a message. Try "give status"')
                        aiy.audio.say('Set project and command before sending a message.')
                elif text[:7] == 'bye bye':
                    running = False
                    aiy.audio.say('Farewell.')
                    print("Exiting program.")
                else:
                    aiy.audio.play_audio(audio, assistant.get_volume())

if __name__ == '__main__':
    main()
