import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# প্রোটোবাফ ফাইলগুলো ইম্পোর্ট করা হলো (লগইনের জন্য এই দুটি প্রয়োজন)
import my_pb2
import output_pb2

# আপনার দেওয়া গেম ভার্সনের ফাইল থেকে ডায়নামিক ডেটা ইম্পোর্ট
from game_version import (
    CLIENT_VERSION,
    CLIENT_VERSION_CODE,
    UNITY_VERSION,
    RELEASE_VERSION,
    MSDK_VERSION,
    USER_AGENT_MODEL,
    ANDROID_OS_VERSION
)

# AES এনক্রিপশন কি (Key) এবং আইভি (IV)
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def encrypt_message(plaintext, key_bytes, iv_bytes):
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_message = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded_message)

def major_login(access_token, open_id, platform_type=4):
    """অ্যাক্সেস টোকেন ব্যবহার করে গেম সার্ভার থেকে ফাইনাল JWT টোকেন জেনারেট করে"""
    try:
        game_data = my_pb2.GameData()
        game_data.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        game_data.game_name = "free fire"
        game_data.game_version = 1
        
        # game_version.py থেকে ডেটা নেওয়া হচ্ছে
        game_data.version_code = CLIENT_VERSION
        game_data.os_info = f"{ANDROID_OS_VERSION} / API-29 (rel.cjw.20220518.114133)"
        
        game_data.device_type = "Handheld"
        game_data.network_provider = "Verizon Wireless"
        game_data.connection_type = "WIFI"
        game_data.screen_width = 1280
        game_data.screen_height = 960
        game_data.dpi = "240"
        game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
        game_data.total_ram = 5951
        game_data.gpu_name = "Adreno (TM) 640"
        game_data.gpu_version = "OpenGL ES 3.0"
        game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
        game_data.ip_address = "172.190.111.97"
        game_data.language = "en"
        game_data.open_id = open_id
        game_data.access_token = access_token
        game_data.platform_type = platform_type
        game_data.field_99 = str(platform_type)
        game_data.field_100 = str(platform_type)

        serialized_data = game_data.SerializeToString()
        encrypted_data = encrypt_message(serialized_data, AES_KEY[:16], AES_IV[:16])
        hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

        url = "https://loginbp.ggpolarbear.com/MajorLogin"
        
        # হেডারে game_version.py এর ডায়নামিক ভ্যালু বসানো হয়েছে
        headers = {
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; {ANDROID_OS_VERSION}; {USER_AGENT_MODEL} Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/octet-stream",
            "Expect": "100-continue",
            "X-Unity-Version": UNITY_VERSION,
            "X-GA": "v1 1",
            "ReleaseVersion": RELEASE_VERSION
        }
        edata = bytes.fromhex(hex_encrypted_data)

        response = requests.post(url, data=edata, headers=headers, timeout=10)

        if response.status_code == 200:
            try:
                example_msg = output_pb2.Garena_420()
                example_msg.ParseFromString(response.content)
                data_dict = {field.name: getattr(example_msg, field.name)
                             for field in example_msg.DESCRIPTOR.fields
                             if field.name not in ["binary", "binary_data", "Garena420"]}
            except:
                data_dict = response.json()

            if data_dict and "token" in data_dict:
                return {"success": True, "jwt_token": data_dict["token"]}
        return {"success": False, "error": "MajorLogin failed"}
    except Exception as e:
        return {"success": False, "error": f"MajorLogin error: {str(e)}"}

# =====================================================================
# ইউজার যে টোকেন বের করতে চায় তার জন্য আলাদা আলাদা ফাংশন
# =====================================================================

def get_access_token_from_uid_pass(uid, password):
    """UID এবং Password দিয়ে শুধুমাত্র Access Token বের করার ফাংশন"""
    oauth_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    
    # game_version.py থেকে ডায়নামিক ইউজার-এজেন্ট
    headers = {
        'User-Agent': f"GarenaMSDK/{MSDK_VERSION}({USER_AGENT_MODEL} ;{ANDROID_OS_VERSION};pt;BR;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }

    try:
        response = requests.post(oauth_url, data=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data and 'open_id' in data:
                return {"success": True, "access_token": data["access_token"], "open_id": data["open_id"]}
        return {"success": False, "error": "Invalid UID or Password"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_access_token_from_eat(eat_token):
    """EAT Token দিয়ে Access Token বের করার ফাংশন"""
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        response = requests.get(url, allow_redirects=True, timeout=30, verify=False)
        
        if 'help.garena.com' in response.url:
            parsed = urlparse(response.url)
            params = parse_qs(parsed.query)
            
            if 'access_token' in params:
                access_token = params['access_token'][0]
                inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
                inspect_response = requests.get(inspect_url, timeout=15, verify=False)
                
                if inspect_response.status_code == 200:
                    token_data = inspect_response.json()
                    if 'open_id' in token_data:
                        return {
                            'success': True,
                            'access_token': access_token,
                            'open_id': token_data['open_id'],
                            'platform_type': token_data.get('platform', 4)
                        }
        return {'success': False, 'error': 'Invalid EAT token'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_jwt_from_access_token(access_token):
    """Access Token দিয়ে ফাইনাল JWT Token বের করার ফাংশন"""
    try:
        inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
        inspect_response = requests.get(inspect_url, timeout=15, verify=False)
        
        if inspect_response.status_code == 200:
            token_data = inspect_response.json()
            if 'open_id' in token_data:
                platform_type = token_data.get('platform', 4)
                open_id = token_data['open_id']
                return major_login(access_token, open_id, platform_type)
        return {'success': False, 'error': 'Invalid Access Token'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_jwt_from_uid_pass(uid, password):
    """UID এবং Password দিয়ে সরাসরি ফাইনাল JWT Token বের করার ফাংশন"""
    access_result = get_access_token_from_uid_pass(uid, password)
    if not access_result['success']:
        return access_result
    
    return major_login(access_result['access_token'], access_result['open_id'])

def get_jwt_from_eat_token(eat_token):
    """EAT Token দিয়ে সরাসরি ফাইনাল JWT Token বের করার ফাংশন"""
    access_result = get_access_token_from_eat(eat_token)
    if not access_result['success']:
        return access_result
    
    return major_login(access_result['access_token'], access_result['open_id'], access_result.get('platform_type', 4))
