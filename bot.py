from flask import Flask, request, Response
from kik import KikApi, Configuration
from kik.messages import messages_from_json, StickerMessage, SuggestedResponseKeyboard, TextResponse, keyboard_message, PictureMessage, TextMessage, ScanDataMessage, LinkMessage, StartChattingMessage, VideoMessage
import requests
import os
import sqlite3
from weather import Weather, Unit

#CONNECT WEATHER
weather = Weather(unit=Unit.CELSIUS)

#DATABASE CONNECTION
conn = sqlite3.connect('weather.db', check_same_thread=False)
c = conn.cursor()

#CREATE TABLE
try: 
    c.execute("""CREATE TABLE data (   
                username text,
                location text           
            )""")
    conn.commit()
    conn.close()
except:
    pass

#KIK CONNECTION

app = Flask(__name__)
kik = KikApi(BOT_USERNAME, BOT_API_KEY)

kik.set_configuration(Configuration(webhook=WEBHOOK))

@app.route('/', methods=['POST'])
def incoming():
    if not kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
        return Response(status=403)
    print("Checking for messages...")
    messages = messages_from_json(request.json['messages'])
    print(str(messages))

    for message in messages:

        def text_message(text):

            textMessage = TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body=text
            )

            return textMessage
        
        def text_message_with_keyboard(text, cusKey):

            textMessage = TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body=text,
                keyboards = cusKey
            )

            return textMessage


        if isinstance(message, StartChattingMessage):
            text = "Hello, My job is to send the weather"
            custom_resp2 = TextResponse("Weather")
            custom_resp2.metadata = message.from_user
            cusKey = [SuggestedResponseKeyboard(responses=[custom_resp2])]
            kik.send_messages([text_message_with_keyboard(text,cusKey)])

        elif isinstance(message, TextMessage):

            print("Message '{}' from '{}'".format(message.body, message.from_user))

            message.body = message.body.lower()

            if len(message.from_user)<=20:

                if message.metadata is None:

                    words_in_messages = message.body.split(' ')
                    first_word = words_in_messages[0]

                    list1 = ['hi','hello','howdy','']

                    if message.body in list1:
                        text = "Do you want to view the weather?\n\nSelect weather to view it!"
                        custom_resp = TextResponse('Set location')
                        custom_resp.metadata = "SETLOCATION"
                        custom_resp2 = TextResponse("Weather")
                        custom_resp2.metadata = message.from_user
                        cusKey = [SuggestedResponseKeyboard(responses=[custom_resp,custom_resp2])]
                        kik.send_messages([text_message_with_keyboard(text,cusKey)])
                    
                    elif message.body=="help":
                        text="Send location to view weather!"
                        cusKey = [SuggestedResponseKeyboard(responses=[TextResponse("Help")])]
                        kik.send_messages([text_message_with_keyboard(text,cusKey)])
                    
                    elif first_word=='set':

                        user_location = message.body.replace('set ','')
                        print(user_location)
                        user_name = message.from_user


                        c.execute('SELECT * FROM data WHERE username=?', (user_name,))
                        r = c.fetchone()
                        if r is None:
                            print('inserting...')
                            c.execute("INSERT INTO data VALUES ('{}','{}')".format(user_name,user_location))
                            conn.commit()
                        else:
                            print('updating...')
                            c.execute("UPDATE data SET location='{}' WHERE username='{}'".format(user_location,user_name))
                            conn.commit()
                        text = "Location Successfully Saved!"
                        custom_resp2 = TextResponse("Weather")
                        custom_resp2.metadata = message.from_user
                        cusKey = [SuggestedResponseKeyboard(responses=[custom_resp2])]
                        kik.send_messages([text_message_with_keyboard(text,cusKey)])
            
                elif message.metadata is not None:


                    if message.metadata=="SETLOCATION":
                        text = "Send your location beginning with 'set' followed by your location\n\n"
                        text += "Example :\n\nSet london"
                        cusKey = [SuggestedResponseKeyboard(responses=[TextResponse("Help")])]
                        kik.send_messages([text_message_with_keyboard(text,cusKey)])
                    

                    elif message.metadata=="CHANGELOCATION":
                        text = "Send your location beginning with 'set' followed by your location\n\n"
                        text += "Example :\n\nSet london"
                        cusKey = [SuggestedResponseKeyboard(responses=[TextResponse("Help")])]
                        kik.send_messages([text_message_with_keyboard(text,cusKey)])
                    

                    elif message.body=="weather":

                        c.execute('SELECT * FROM data WHERE username=?', (message.metadata,))
                        r = c.fetchone()

                        if r is not None:
                            loc_name = r[1]
                            location = weather.lookup_by_location(loc_name)

                            condition = location.condition
                            text = 'Weather in '+loc_name+' is '+condition.text
                            custom_resp = TextResponse('Change location')
                            custom_resp.metadata = "CHANGELOCATION"
                            cusKey = [SuggestedResponseKeyboard(responses=[custom_resp])]
                            kik.send_messages([text_message_with_keyboard(text,cusKey)])
                        else:
                            text = "Your location is not set"
                            custom_resp = TextResponse('Set location')
                            custom_resp.metadata = "SETLOCATION"
                            cusKey = [SuggestedResponseKeyboard(responses=[custom_resp])]
                            kik.send_messages([text_message_with_keyboard(text,cusKey)])

            else:
                text = "Hi, Please PM the bot to view weather!"
                kik.send_messages([text_message(text)])

        elif isinstance(message, PictureMessage) or isinstance(message, StickerMessage) or isinstance(message, ScanDataMessage) or isinstance(message, VideoMessage) or isinstance(message, LinkMessage):
            message_to_send = "Whoops! Looks like i can't deal with your message!\n\n"
            kik.send_messages([
                TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body=message_to_send,
                    keyboards=[SuggestedResponseKeyboard(
                        responses=[TextResponse("Weather")])]
                )])    

    return Response(status=200)


if __name__ == "__main__": 
    port = int(os.environ.get('PORT', 8080))
    app.run(host='', port=port, debug=True)
