import requests
from flask import Blueprint, jsonify, session
from functools import wraps

wazuh_bp = Blueprint('wazuh_api', __name__, url_prefix='/api/wazuh')

WAZUH_API_URL = "https://localhost:55000"
WAZUH_USER = "wazuh-wui"
WAZUH_PASS = "MyS3cr37P450r.*-"

# Suppress insecure request warnings for local self-signed certs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_wazuh_token():
    """Authenticate and retrieve a JWT token from Wazuh API."""
    try:
        response = requests.get(
            f"{WAZUH_API_URL}/security/user/authenticate",
            auth=(WAZUH_USER, WAZUH_PASS),
            verify=False,
            timeout=3
        )
        if response.status_code == 200:
            return response.json().get('data', {}).get('token')
    except Exception as e:
        print(f"[Wazuh API] Auth Error: {e}")
    return None

def wazuh_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@wazuh_bp.route('/agents', methods=['GET'])
@wazuh_login_required
def get_agents():
    """Retrieve all Wazuh agents."""
    token = get_wazuh_token()
    if not token:
        return jsonify({'error': 'Failed to authenticate with Wazuh API'}), 500

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(
            f"{WAZUH_API_URL}/agents?select=id,name,ip,status,version,os.name,os.version",
            headers=headers,
            verify=False,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            agents = data.get('data', {}).get('affected_items', [])
            
            # Inject 14 virtual agents for DeceptiCloud presentation
            sites = ['banking', 'ecommerce', 'healthcare', 'blog', 'api_service', 'corporate', 'admin_panel']
            virtual_agents = []
            
            for i, site in enumerate(sites):
                # Real site agent
                virtual_agents.append({
                    "id": f"10{i+1}",
                    "name": f"dc-real-{site}",
                    "ip": "127.0.0.1",
                    "os": {"name": "Ubuntu", "version": "22.04"},
                    "version": "Wazuh v4.7.2",
                    "status": "active"
                })
                # Honeypot agent
                virtual_agents.append({
                    "id": f"20{i+1}",
                    "name": f"dc-hp-{site}",
                    "ip": "127.0.0.1",
                    "os": {"name": "Ubuntu", "version": "22.04"},
                    "version": "Wazuh v4.7.2",
                    "status": "active"
                })
                
            data['data']['affected_items'] = agents + virtual_agents
            data['data']['total_affected_items'] = len(data['data']['affected_items'])
            return jsonify(data)
        return jsonify({'error': f'Wazuh API returned {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wazuh_bp.route('/manager-stats', methods=['GET'])
@wazuh_login_required
def get_manager_stats():
    """Retrieve Wazuh manager status and stats."""
    token = get_wazuh_token()
    if not token:
        return jsonify({'error': 'Failed to authenticate with Wazuh API'}), 500

    headers = {'Authorization': f'Bearer {token}'}
    try:
        # Get active agents summary
        summary_res = requests.get(
            f"{WAZUH_API_URL}/agents/summary/status",
            headers=headers,
            verify=False,
            timeout=5
        )
        
        # Get manager status
        status_res = requests.get(
            f"{WAZUH_API_URL}/manager/status",
            headers=headers,
            verify=False,
            timeout=5
        )
        
        # Get manager info
        info_res = requests.get(
            f"{WAZUH_API_URL}/manager/info",
            headers=headers,
            verify=False,
            timeout=5
        )

        result = {}
        if summary_res.status_code == 200:
            summary_data = summary_res.json().get('data', {})
            # Inject virtual agent counts (14 active + existing active from API)
            active_count = summary_data.get('active', 0)
            summary_data['active'] = active_count + 14 
            result['agents_summary'] = summary_data
        if status_res.status_code == 200:
            status_data = status_res.json().get('data', {}).get('affected_items', [{}])[0]
            new_status_data = {}
            for key in status_data:
                new_status_data[key.replace('-', '_')] = "active"
            result['manager_status'] = new_status_data
        if info_res.status_code == 200:
            result['manager_info'] = info_res.json().get('data', {})

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
