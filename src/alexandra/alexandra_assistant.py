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

import aiy.assistant.grpc
import aiy.audio
import aiy.voicehat

# Added by Thomas
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)

def send_request(nick_name):
    try:
        response = requests.get(
            url="https://devices.alexandra.dk/webUI/sensors/nick/" + nick_name + "/traincontrol.json",
            headers={
                "Authorization": "Basic c3BlYWtVc2VyOkxpdHRsZUJpdGNoOTM=",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
        parsed_json = response.json()
        return parsed_json['sensorNames'][0]
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

def send_message(message):
    deviceId = send_request("little bitch")
    if deviceId is None:
        return

    client = mqtt.Client("LOCALCONNECTION") #create new instance
    client.connect("localhost") #connect to broker
    client.publish("/iot/commands/aiy/" + deviceId, message)#publish$
    print('I have send a message')

def main():
    status_ui = aiy.voicehat.get_status_ui()
    status_ui.status('starting')
    assistant = aiy.assistant.grpc.get_assistant()
    button = aiy.voicehat.get_button()
    with aiy.audio.get_recorder():
        while True:
            status_ui.status('ready')
            print('Press the button and speak')
            button.wait_for_press()
            status_ui.status('listening')
            print('Listening...')
            text, audio = assistant.recognize()
            if text:
                print('You said "', text, '"')
            if audio:
                print('You said "', text, '"')
                if text[:7] == 'command':
                    aiy.audio.say('Command received ' + text[8:])
                    send_message(text[8:])
                else:
                    aiy.audio.play_audio(audio, assistant.get_volume())


if __name__ == '__main__':
    main()
