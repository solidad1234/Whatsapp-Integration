import frappe
import requests
from frappe import _

WACLIENT_API_URL = "https://api.waclient.com/send"

def get_settings():
    try:
        settings = frappe.get_single("WhatsApp Settings")
        if not settings.is_active:
            return None
        return settings
    except frappe.DoesNotExistError:
        return None

def log_message(recipient, message, status, error_message=None):
    try:
        doc = frappe.get_doc({
            "doctype": "WhatsApp Log",
            "recipient": recipient,
            "message": message,
            "status": status,
            "error_message": error_message
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create WhatsApp Log: {str(e)}", "WhatsApp Integration Error")

def send_whatsapp_message(number, message):
    settings = get_settings()
    if not settings:
        return

    payload = {
        "number": number,
        "type": "text",
        "message": message,
        "instance_id": settings.instance_id,
        "access_token": settings.access_token
    }

    try:
        response = requests.post(WACLIENT_API_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        resp_data = response.json()
        if resp_data.get("status") == "success":
            log_message(number, message, "Success")
        else:
            log_message(number, message, "Failed", frappe.as_json(resp_data))
            
    except Exception as e:
        frappe.log_error(f"WhatsApp Text Send Error: {str(e)}", "WhatsApp Integration Error")
        log_message(number, message, "Failed", str(e))

def send_whatsapp_media(number, media_url, message="", filename=""):
    settings = get_settings()
    if not settings:
        return

    payload = {
        "number": number,
        "type": "media",
        "media_url": media_url,
        "instance_id": settings.instance_id,
        "access_token": settings.access_token
    }
    
    if message:
        payload["message"] = message
        
    if filename:
        payload["filename"] = filename

    try:
        response = requests.post(WACLIENT_API_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        resp_data = response.json()
        if resp_data.get("status") == "success":
            log_message(number, f"Media: {media_url}\n{message}", "Success")
        else:
            log_message(number, f"Media: {media_url}\n{message}", "Failed", frappe.as_json(resp_data))
            
    except Exception as e:
        frappe.log_error(f"WhatsApp Media Send Error: {str(e)}", "WhatsApp Integration Error")
        log_message(number, f"Media: {media_url}\n{message}", "Failed", str(e))

@frappe.whitelist(allow_guest=True)
def incoming_message(**kwargs):
    # This acts as the auto-responder endpoint
    # The payload structure depends on what Waclient sends
    data = frappe.request.get_json() if frappe.request else kwargs
    
    # Example logic (adjust based on actual Waclient webhook payload):
    # sender = data.get("sender")
    # message = data.get("text")
    # if sender and message == "Hi":
    #     send_whatsapp_message(sender, "Hello! This is an auto-reply.")
    
    return {"status": "success"}

def set_webhook():
    settings = get_settings()
    if not settings or not settings.webhook_url:
        return
        
    url = "https://waclient.com/docs/whatsapp-web-api/instances/set-webhook"
    # Note: actual endpoint might be different as per Waclient API spec, but this provides the wrapper
    # Waclient documentation says Set Webhook POST /set-webhook
    api_url = "https://api.waclient.com/set-webhook" 
    
    payload = {
        "webhook_url": settings.webhook_url,
        "enable": True,
        "instance_id": settings.instance_id,
        "access_token": settings.access_token
    }
    
    try:
        response = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        frappe.log_error(f"WhatsApp Set Webhook Error: {str(e)}", "WhatsApp Integration Error")
