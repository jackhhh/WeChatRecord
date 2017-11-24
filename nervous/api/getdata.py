# -*- coding: UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )
import os, base64, datetime, hashlib, hmac, json 
import requests
# ************* 请求参数 *************
method = 'GET'
host = 'api.gsdata.cn'
app_id = '167'
secret_key = 'Mef9BkjBM1XqMDmLE2FtPe2pJzXUBirZ'

def json_encode(input):
    result_string = ''
    flag = 0
    input.sort()
    for keys in input:
        if flag == 1:
            result_string += '&'
        result_string += keys[0]
        result_string += '='
        result_string += str(keys[1])
        flag = 1
    return result_string

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, serviceName):
    kDate = sign(('GSDATA' + key).encode('utf-8'), dateStamp)
    kService = sign(kDate, serviceName)
    kSigning = sign(kService, 'gsdata_request')
    return kSigning

def standard_request(service, request_parameters):
    global method, host, app_id, secret_key

    if app_id is None or secret_key is None:
        print 'No access key is available.'
        sys.exit()
   
    t = datetime.datetime.utcnow()
    gsdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope

    canonical_uri = service 
    canonical_querystring = request_parameters
    canonical_headers = 'host:' + host + '\n' + 'x-gsdata-date:' + gsdate

    signed_headers = 'host;x-gsdata-date'

    payload_hash = hashlib.sha256('').hexdigest()

    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers +'\n'+ payload_hash
    print 'canonical_request: %s\n' % canonical_request

    algorithm = 'GSDATA-HMAC-SHA256'
    string_to_sign = algorithm + '\n' +  gsdate + '\n' +  hashlib.sha256(canonical_request).hexdigest()
    signing_key = getSignatureKey(secret_key, datestamp, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = algorithm + ' ' + 'AppKey=' + app_id + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    headers = {'x-gsdata-date':gsdate, 'Authorization':authorization_header}

    # ************* SEND THE REQUEST *************
    request_url = 'http://'+host+service + '?' + canonical_querystring
    r = requests.get(request_url, headers=headers)
    print '\nRESPONSE++++++++++++++++++++++++++++++++++++'
    print 'Response code: %d\n' % r.status_code
    #print r.text

    return r.text

def get_dict(url, paras):
    output = standard_request(url, json_encode(paras.items()))
    d = json.loads(output)
    return d
