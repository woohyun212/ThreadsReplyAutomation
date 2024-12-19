import json
import urllib.parse
import os
import time
import requests
from random import choice

# Threads Webhook 인증용 토큰
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

EMOJIS = "~ 😊 🥰 🥺 🤭 😻 💖 💞 🎀 ✨ 🌸 🌷 🌈 🐣 🐥 🐰 🐹 🐱 🐶 🦊 🐼 🐨 🐻 🍭 🍬 🌺 💗 💘 💝 💟 💜 💚 💛 💙 🤎 🤍 ❤️‍🔥 💓 💕 💌 🩷 🩰 🎉 🧸 🍑 🍓 🍉 🦄 🦋 🌼 🌻 🌟 ✨".split()

def lambda_handler(event, context):
    # API Gateway Proxy Integration 이벤트 형식
    http_method = event.get('httpMethod')
    query_params = event.get('queryStringParameters', {}) if event.get('queryStringParameters') else {}
    body = event.get('body', None)
    # 로그 분석용
    print(body)
    
    if http_method == 'GET':
        # Webhook 인증 단계 (subscribe 요청)
        hub_mode = query_params.get('hub.mode')
        hub_verify_token = query_params.get('hub.verify_token')
        hub_challenge = query_params.get('hub.challenge')
        
        if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
            # 정상 인증 시 hub_challenge 반환
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "text/plain" },
                "body": hub_challenge
            }
        else:
            # 인증 실패 시 403 반환
            return {
                "statusCode": 403,
                "body": "Verification token mismatch"
            }

    elif http_method == 'POST':
        # Webhook 이벤트 처리
        try:
            # body가 JSON 문자열이므로 파싱
            data = json.loads(body)
            # print(data)
            reply = data['values'][0]['value']
            if reply["username"] != reply["root_post"]["username"]:
                message = f"스하리" + choice(EMOJIS)
                post_text_reply_to_comment(reply['id'], message, ACCESS_TOKEN)

            return {
                "statusCode": 200,
                "body": json.dumps({"status": "ok"})
            }
        except Exception as e:
            print("Error processing webhook data:", e)
            return {
                "statusCode": 500,
                "body": "Internal Server Error"
            }

    else:
        # 지원하지 않는 메소드에 대한 처리
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }

def post_text_reply_to_comment(comment_id, message, access_token):
   
    """특정 댓글에 대댓글을 달기 위한 함수.

    Parameters:
        comment_id (str): 대댓글을 달고자 하는 대상 댓글의 ID
        message (str): 작성할 대댓글 내용
        access_token (str): Thread 액세스 토큰(댓글 작성 권한 포함)

    Returns:
        dict: API 응답 결과(JSON 파싱된 딕셔너리)
    """
    api_version = "v1.0"
    url = f"https://graph.threads.net/{api_version}/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # try:
    # Create Media Container
    response = requests.post(url + "me/threads", headers=headers, 
        json={
            "media_type": "TEXT_POST",
            "reply_to_id": comment_id,
            "text": message
        })
    # 요청 성공 시 Media Container ID 획득, 400/403 등일 경우 에러 메시지 반환
    if response.status_code == 200:
        media_container_id = response.json()["id"]
    else:
        print(response.json())
        return {"error": response.json(), "status_code": response.status_code}

    # Check Media Container Status
    status = ""
    while status != "FINISHED":
        response = requests.get(url + media_container_id, headers=headers)
        status = response.json()["status"]
        print("Check", response.json())
        # 필요시
        # time.sleep(1)
    
    # Publish Media Container
    response = requests.post(url + "me/threads_publish", headers=headers, 
        json={
            "creation_id": media_container_id
        })
    print("Publish :", response.json())
    # except Exception as e:
    #     return {'statusCode': 500}

