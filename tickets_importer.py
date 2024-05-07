'''
---> IMPORTANT <---

Please visit this link to get instructions of how to use this code: 
https://everlasting-eustoma-5c2.notion.site/NinjaOne-Bulk-Uploader-Ticketing-2df47979219d4973a5bcc06fd8748ca9


'''

import requests
import pandas as pd
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# ENTER YOUR API KEYS HERE
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
INSTANCE = 'YOUR_INSTANCE.rmmservice.eu'
# STATIC URL
REDIRECT_URL = 'http://localhost:3000/'
CREATE_TICKET_URL = "https://YOUR_INSTANCE.rmmservice.eu/v2/ticketing/ticket"

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        if 'code' in query_components:
            self.server.auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>NinjaOne</h1><br /><p>An authorisation code has been received. You can close this tab/window now.</p>')
        else:
            self.send_error(400, 'An Error Occurred')

def get_oauth_code(auth_url, redirect_url):
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, RequestHandler)
    webbrowser.open(auth_url)
    httpd.handle_request()
    httpd.server_close()
    return httpd.auth_code

def get_access_token(auth_code):
    auth_body = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'redirect_uri': REDIRECT_URL 
    }
    try:
        auth_result = requests.post(f"https://{INSTANCE}/ws/oauth/token", data=auth_body)
        auth_result.raise_for_status()
        refresh_token = auth_result.json().get('refresh_token')

        auth_body = {
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': refresh_token
        }
        auth_result = requests.post(f"https://{INSTANCE}/ws/oauth/token", data=auth_body)
        auth_result.raise_for_status()
        return auth_result.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print("An error occurred while obtaining access token:", e)
        return None

def create_ticket(access_token, payload):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(CREATE_TICKET_URL, json=payload, headers=headers)
    print("Response content:", response.content) 
    return response.json()

def prepare_payload_from_csv(csv_file):
    try:
        # MANDANTORY ATTRIBUTES
        df = pd.read_csv(csv_file, sep=';')
        df['clientId'] = df['clientId'].astype('int32')
        df['ticketFormId'] = df['ticketFormId'].astype('int32')
        df['description.public'] = df['description.public'].astype(bool)
        df['status'] = df['status'].astype(str)
        df['type'] = df['type'].astype(str)

        # OPTIONAL ATTRIBUTES

        payload = []
        for index, row in df.iterrows():
            ticket_payload = {
                # MANDANTORY ATTRIBUTES
                "clientId": row['clientId'],
                "ticketFormId": row['ticketFormId'],
                "subject": row['subject'],
                "description": {
                    "public": row['description.public'],
                    "body": row['description.body'],
                },
                "status": row['status'],
                "type": row['type'],

                # OPTIONAL ATTRIBUTES
            }
            payload.append(ticket_payload)
        
        return payload
    except Exception as e:
        print("An error occurred while preparing payload from CSV:", e)
        return None


try:
    auth_url = f"https://{INSTANCE}/ws/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URL}&scope=monitoring%20management%20offline_access&state=STATE"
    auth_code = get_oauth_code(auth_url, REDIRECT_URL)
    access_token = get_access_token(auth_code)
    
    if access_token:
        # Define local path here
        csv_file = "ENTER_PATH_HERE/bulk-import-tickets.csv"
        payload = prepare_payload_from_csv(csv_file)
        
        if payload:
            for ticket_payload in payload:
                ticket_response = create_ticket(access_token, ticket_payload)
                if ticket_response:
                    print("Ticket created successfully:", ticket_response)
                else:
                    print("Failed to create ticket.")
        else:
            print("Failed to prepare payload from CSV.")
    else:
        print("Failed to obtain access token.")
except Exception as e:
    print("An error occurred:", e)
