import subprocess
import json
import time
import sys
import os

TARGET_EMAILS = ["testuser001@outlook.com", "testuser001@outlook.in"]
PROCESSED_IDS = set()
START_TIME = time.time()
DURATION = 3600 # 1 hour

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    sys.stdout.flush()

def get_envelopes():
    for attempt in range(3):
        try:
            result = subprocess.run(
                ["himalaya", "envelope", "list", "-o", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            log(f"Error listing envelopes (Attempt {attempt+1}/3): {e}")
            time.sleep(5)
    return []

def generate_reply_with_ollama(email_content):
    log("Generating reply with Ollama (llama3.2:3b)...")
    prompt = (
        "You are a helpful and polite email assistant. "
        "Your task is to write a reply to the email provided below. "
        "Keep the reply concise, professional, and friendly. "
        "Do NOT include the subject line or headers in your output. "
        "Do NOT include placeholders like '[Your Name]'. "
        "Just write the body of the reply.\n\n"
        "--- START OF EMAIL ---\n"
        f"{email_content}\n"
        "--- END OF EMAIL ---\n\n"
        "Reply:"
    )
    
    try:
        # Use llama3.2:3b as requested (local llama model)
        result = subprocess.run(
            ["ollama", "run", "llama3.2:3b", prompt],
            capture_output=True,
            text=True,
            encoding='utf-8', 
            check=True
        )
        reply = result.stdout.strip()
        
        # Basic cleanup if the model outputs something weird
        if not reply:
            log("Warning: Ollama returned empty response. Using fallback.")
            return "Thank you for your email. I have received your message."
            
        return reply
    except Exception as e:
        log(f"Error generating reply with Ollama: {e}")
        return "Thank you for your email. I have received your message."

def send_reply(email_id, subject):
    log(f"Processing reply for email ID: {email_id}, Subject: {subject}")
    
    # 1. Read the content of the email to reply to
    email_content = ""
    try:
        read_proc = subprocess.run(
            ["himalaya", "message", "read", str(email_id)], 
            capture_output=True, 
            text=True, 
            check=True
        )
        email_content = read_proc.stdout
        log(f"--- FULL CONTENT OF EMAIL {email_id} ---\n{email_content}\n--- END CONTENT ---")
    except Exception as e:
        log(f"Error reading email {email_id}: {e}")
        return False

    # 2. Generate the reply body using Ollama
    reply_body = generate_reply_with_ollama(email_content)
    log(f"Generated reply content (first 50 chars): {reply_body[:50]}...")
    
    # 3. Create the reply template with Himalaya
    try:
        cmd_template = ["himalaya", "template", "reply", str(email_id), reply_body]
        result = subprocess.run(cmd_template, capture_output=True, text=True, check=True)
        
        reply_eml_content = result.stdout
        
        with open("reply.eml", "w") as f:
            f.write(reply_eml_content)
            
        # 4. Send the reply
        with open("reply.eml", "r") as f:
            # We catch CalledProcessError to inspect stderr for the specific IMAP error
            proc = subprocess.run(["himalaya", "message", "send"], stdin=f, capture_output=True, text=True)
            
            if proc.returncode != 0:
                # Check if it's the known "cannot add IMAP message" error
                if "cannot add IMAP message" in proc.stderr:
                    log(f"Warning: Failed to save to Sent folder (IMAP error), but email likely sent. Treating as success.")
                else:
                    # Genuine error
                    raise subprocess.CalledProcessError(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)
            
        log(f"Sent reply to ID {email_id}")
        if os.path.exists("reply.eml"):
            os.remove("reply.eml")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Error sending reply (CalledProcessError): {e}")
        if e.stderr:
            log(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        log(f"Error sending reply: {e}")
        return False

def main():
    log("Starting AI-powered auto-reply bot for 1 hour...")
    
    # Initial scan to populate PROCESSED_IDS with EXISTING emails to avoid replying to old ones
    # log("Initializing: Scanning existing emails to ignore...")
    # initial_envelopes = get_envelopes()
    # for env in initial_envelopes:
    #     eid = env.get("id")
    #     PROCESSED_IDS.add(eid)
    # log(f"Ignored {len(PROCESSED_IDS)} existing emails.")
    pass
    
    while time.time() - START_TIME < DURATION:
        elapsed = time.time() - START_TIME
        remaining = int((DURATION - elapsed) / 60)
        log(f"Checking for new emails... (Time remaining: {remaining} min)")
        
        envelopes = get_envelopes()
        
        targets = []
        for env in envelopes:
            sender_info = env.get("from", {})
            sender_addr = ""
            if isinstance(sender_info, dict):
                sender_addr = sender_info.get("addr", "")
            else:
                sender_addr = str(sender_info)
            
            if any(target in sender_addr for target in TARGET_EMAILS):
                targets.append(env)
        
        # Sort by ID descending (newest first)
        targets.sort(key=lambda x: int(x.get("id", 0)) if str(x.get("id", "0")).isdigit() else x.get("id"), reverse=True)
        
        processed_count = 0
        
        # Only check the LATEST email.
        if targets:
            latest = targets[0]
            eid = latest.get("id")
            if eid not in PROCESSED_IDS:
                log(f"Found new target email: ID {eid} from {latest.get('from', {}).get('addr')}")
                if send_reply(eid, latest.get("subject", "No Subject")):
                    PROCESSED_IDS.add(eid)
                    processed_count += 1
        
        if processed_count == 0:
            log("No new target emails found.")
        
        log("Waiting 1 minute...")
        time.sleep(60)

if __name__ == "__main__":
    main()
