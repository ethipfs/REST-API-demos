#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-12-20 15:40:03
# @Author  : KlausQiu
# @QQ      : 375235513
# @github  : https://github.com/KlausQIU

import base64
import datetime
import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature 
# 此处填写APIKEY

ACCESS_KEY = ""
SECRET_KEY = ""

# Need to replace with the actual value generated from below command
# openssl ecparam -name secp256k1 -genkey -noout -out secp256k1-key.pem 
PRIVATE_KEY = open("secp256k1-key.pem", "rb").read()

# API request URL
MARKET_URL = "https://api.huobi.pro"
TRADE_URL = "https://api.huobi.pro"

# Can first request to call get_accounts()to find the target acct_id,later can just specify the actual acc_id in the api call 
ACCOUNT_ID = None

#'Timestamp': '2017-06-02T06:13:49'

def http_get_request(url, params, add_to_headers=None):
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = urllib.parse.urlencode(params)
    response = requests.get(url, postdata, headers=headers, timeout=5) 
    try:
        
        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        print("httpGet failed, detail is:%s,%s" %(response.text,e))
        return


def http_post_request(url, params, add_to_headers=None):
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    response = requests.post(url, postdata, headers=headers, timeout=10)
    try:
        
        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        print("httpPost failed, detail is:%s,%s" %(response.text,e))
        return


def api_key_get(params, request_path):
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_url = TRADE_URL
    host_name = urllib.parse.urlparse(host_url).hostname
    host_name = host_name.lower()
    signature = createSign(params, method, host_name, request_path, SECRET_KEY)
    params['Signature'] = signature
    params['PrivateSignature'] = createPrivateSignature(signature)
    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post(params, request_path):
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}

    host_url = TRADE_URL
    host_name = urllib.parse.urlparse(host_url).hostname
    host_name = host_name.lower()
    signature = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    params_to_sign['Signature'] = signature
    params_to_sign['PrivateSignature'] = createPrivateSignature(signature)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params)


def createSign(pParams, method, host_url, request_path, secret_key):
    sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')
    secret_key = secret_key.encode(encoding='UTF8')

    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature


def createPrivateSignature(context):
    data = bytes(context, encoding='utf8')
    # Read the pri_key_file
    digest = hashes.Hash( hashes.SHA256(), default_backend())

    digest.update(data)
    dgst = digest.finalize()
    skey = load_pem_private_key( PRIVATE_KEY, password=None, backend=default_backend())

    sig_data = skey.sign( data, ec.ECDSA(hashes.SHA256()))
    sig_r, sig_s = decode_dss_signature(sig_data)

    sig_bytes = b''
    key_size_in_bytes = bit_to_bytes(skey.public_key().key_size)
    sig_r_bytes = sig_r.to_bytes(key_size_in_bytes, "big")
    sig_bytes += sig_r_bytes
    #print("ECDSA signature R: {:s}".format(sig_r_bytes.hex()))
    sig_s_bytes = sig_s.to_bytes(key_size_in_bytes, "big")
    sig_bytes += sig_s_bytes
  #  print("ECDSA signature S: {:s}".format(sig_s_bytes.hex()))
    # print("ECDSA signautre: {:s}".format(sig_bytes.hex()))
    #print("ECDSA signautre: " + str(base64.b64encode(sig_bytes)))
    return base64.b64encode(sig_bytes)

def bit_to_bytes(a):
    return (a + 7) // 8