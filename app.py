import streamlit as st
import anthropic
import os
import re
import glob
from datetime import datetime
from fpdf import FPDF
import base64

# Page Configuration
st.set_page_config(
    page_title="PocketPA | Care Assistant",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Constants - API key should be stored in Streamlit secrets
API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
MODEL_NAME = "claude-opus-4-20250514"
MEMORY_DIR = os.path.join("memory", "staff-contexts")
DRAFT_FILE = "current_draft_session.txt"

# Ensure memory directory exists
os.makedirs(MEMORY_DIR, exist_ok=True)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #ffffff;
    }

    .main-header {
        background: linear-gradient(135deg, #006064 0%, #00838F 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        font-weight: 600;
        margin: 0;
        font-size: 1.8rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 5px 0 0 0;
        font-size: 0.9rem;
    }
    .status-badge {
        background-color: rgba(255,255,255,0.2);
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        float: right;
    }

    .stChatMessage {
        background-color: transparent;
        border: none;
    }
    
    .user-bubble {
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: inline-block;
        max-width: 85%;
        margin-left: auto;
        text-align: right;
    }

    .assistant-bubble {
        background-color: #F5F5F5;
        color: #333333;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: inline-block;
        max-width: 90%;
    }

    .stChatInput {
        padding-bottom: 20px;
    }
    .stChatInput textarea {
        border-radius: 25px !important;
        border: 1px solid #E0E0E0;
        padding: 12px 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stChatInput textarea:focus {
        border-color: #00838F;
        box-shadow: 0 0 0 2px rgba(0,131,143,0.2);
    }

    .report-box {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 1px solid #E0E0E0;
        border-top: 4px solid #00838F;
        padding: 25px;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        white-space: pre-wrap;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #EFF2F5;
    }
    
    /* Sidebar text colors */
    section[data-testid="stSidebar"] * {
        color: #333333 !important;
    }
    
    /* Sidebar buttons - ensure visible text */
    section[data-testid="stSidebar"] button {
        color: #333333 !important;
        background-color: #E8E8E8 !important;
        border: 1px solid #CCCCCC !important;
    }
    
    section[data-testid="stSidebar"] button[kind="primary"] {
        color: #FFFFFF !important;
        background-color: #00838F !important;
        border: none !important;
    }
    
    /* Sidebar textarea and selectbox */
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] input {
        color: #333333 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Selectbox dropdown */
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #333333 !important;
    }
    
    /* General button styling */
    .stButton button {
        border-radius: 20px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .stProgress > div > div > div > div {
        background-color: #00838F;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_system_context():
    """Load context from markdown files."""
    agents_content = ""
    skill_content = ""
    
    # Load AGENTS.md
    agents_path = "AGENTS.md"
    if os.path.exists(agents_path):
        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                agents_content = f.read()
        except Exception as e:
            st.error(f"Error loading {agents_path}: {e}")
    
    # Load skills/incident-report.md
    skills_path = os.path.join("skills", "incident-report.md")
    if os.path.exists(skills_path):
        try:
            with open(skills_path, "r", encoding="utf-8") as f:
                skill_content = f.read()
        except Exception as e:
            st.error(f"Error loading {skills_path}: {e}")
            
    return agents_content, skill_content

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'PocketPA Incident Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(report_text):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Handle simple markdown-like headers in report
    for line in report_text.split('\n'):
        if line.isupper() and len(line) > 5 and ":" not in line:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, line, 0, 1)
            pdf.set_font("Arial", size=11)
        else:
            # Replace unsupported characters if any
            clean_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, clean_line)
            
    return pdf.output(dest='S').encode('latin-1')

def save_report_to_file(content, is_formal_report=False):
    """Save content to a file in memory/staff-contexts/."""
    if not content:
        return False, "No content to save."
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "FORMAL_INCIDENT_REPORT" if is_formal_report else "conversation_log"
    filename = f"{prefix}_{timestamp}.txt"
    filepath = os.path.join(MEMORY_DIR, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Saved to {filepath}"
    except Exception as e:
        return False, f"Failed to save: {e}"

def save_draft(messages):
    """Auto-save current session to draft file."""
    try:
        with open(DRAFT_FILE, 'w', encoding='utf-8') as f:
            for msg in messages:
                # Sanitise content for storage
                content = msg['content'].replace("|||", "")
                f.write(f"{msg['role']}::{content}|||")
    except Exception:
        pass 

def load_draft():
    """Load session from draft file if exists."""
    messages = []
    if os.path.exists(DRAFT_FILE):
        try:
            with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
                data = f.read()
                chunks = data.split('|||')
                for chunk in chunks:
                    if '::' in chunk:
                        role, content = chunk.split('::', 1)
                        if role and content:
                            messages.append({"role": role, "content": content})
        except Exception:
            pass
    return messages

def calculate_progress(messages):
    """Estimate report progress based on gathered fields."""
    full_text = " ".join([m['content'].lower() for m in messages])
    
    fields = {
        "Date/Time": False,
        "Location": False,
        "Child ID": False,
        "Staff Present": False,
        "Description": False,
        "Emotional State": False,
        "Action Taken": False,
        "Injuries": False
    }
    
    # Enhanced patterns
    if re.search(r'\b(date|time|happened at|when)\b', full_text): fields["Date/Time"] = True
    if re.search(r'\b(where|location|room|lounge|garden|bedroom)\b', full_text): fields["Location"] = True
    if re.search(r'\b(child|resident|who|initials|name|him|her)\b', full_text): fields["Child ID"] = True
    if re.search(r'\b(staff|witness|present|saw|colleague)\b', full_text): fields["Staff Present"] = True
    if len(messages) > 4: fields["Description"] = True 
    if re.search(r'\b(emotion|feeling|upset|calm|angry|crying|distressed|happy)\b', full_text): fields["Emotional State"] = True
    if re.search(r'\b(did|action|intervention|called|helped|comforted|administered)\b', full_text): fields["Action Taken"] = True
    if re.search(r'\b(hurt|injury|mark|bruise|cut|scratch|wound|no injur)\b', full_text): fields["Injuries"] = True
    
    completed = sum(fields.values())
    total = len(fields)
    return completed / total, fields

def generate_formal_report(messages):
    """Generate a formal incident report using Claude."""
    try:
        client = anthropic.Anthropic(api_key=API_KEY)
        
        conversation_text = ""
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            conversation_text += f"{role}: {content}\n\n"

        system_prompt = """You are generating a formal incident report for a UK care home. Use the information provided to create a comprehensive, compliant report. Be professional and thorough.

Report format:
INCIDENT REPORT
BASIC INFORMATION
Date: [date]
Time: [time]
Location: [location]
Child: [name/ID]
Reporting Staff: [staff name]
Report ID: [auto-generated]

INCIDENT DESCRIPTION
[Full narrative of what happened - expand on raw notes to be comprehensive]

PEOPLE INVOLVED
Staff Present: [names]
Witnesses: [names or "None"]

CHILD'S EMOTIONAL STATE
Before: [description]
During: [description]
After: [description]

IMMEDIATE ACTION TAKEN
[Actions and interventions]

INJURIES / DAMAGE
[Description or "None reported"]

FOLLOW-UP REQUIRED
[Yes/No and details]

COMPLIANCE NOTES
[Assess if anything is missing or needs attention]

Report Generated: [timestamp]
Status: AWAITING STAFF APPROVAL"""

        user_message = f"Please generate the incident report based on this conversation:\n\n{conversation_text}"

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        return response.content[0].text
        
    except anthropic.RateLimitError:
        return "⚠️ PocketPA is currently busy (Rate Limit Reached). Please wait a moment and try again."
    except anthropic.APIError as e:
        return f"⚠️ Connection Error: {str(e)}"
    except Exception as e:
        return f"⚠️ Error generating report: {str(e)}"

def get_claude_response(messages, agents_context, skill_context):
    """Generate response from Claude API with robustness."""
    try:
        client = anthropic.Anthropic(api_key=API_KEY)
        
        history_to_send = []
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        
        for msg in recent_messages:
            history_to_send.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            
        system_prompt = f"""You are PocketPA, an AI assistant for care home staff.

{agents_context}

SKILL INSTRUCTIONS:
{skill_context}

Respond naturally and empathetically. Guide them through incident reporting by asking ONE question at a time. Be warm and patient.

Make responses feel human:
- "Take your time, I'm here to help"
- "I understand this can be stressful"
- "Let me make sure I have everything..."
- Use staff member's language and tone
- Be concise but thorough.
- If the user is stressed, reassure them first.

IMPORTANT: When you have gathered ALL required information (Date, Time, Location, Child, Staff, Description, People, Actions, Injuries) according to the skill instructions, YES/NO for specific details is fine if covered, output the tag <GENERATE_REPORT> at the very end of your response."""

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2048,
            system=system_prompt,
            messages=history_to_send
        )
        
        return response.content[0].text
        
    except anthropic.RateLimitError:
        return "⚠️ PocketPA is thinking too hard! (Rate Limit). Please wait a few seconds."
    except anthropic.APIError as e:
        return f"⚠️ I'm having trouble connecting to the network right now. ({str(e)})"
    except Exception as e:
        return f"⚠️ Something went wrong: {str(e)}"

# --- Main App Logic ---

# Initialize session state with draft recovery
if "messages" not in st.session_state:
    recovered_msgs = load_draft()
    if recovered_msgs:
        st.session_state.messages = recovered_msgs
        st.toast("Restored previous session draft.", icon="📂")
    else:
        st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("PocketPA 🛡️")
    st.markdown("*Making care documentation effortless*")
    
    # Progress Section
    st.divider()
    prog_val, prog_fields = calculate_progress(st.session_state.messages)
    st.caption(f"Report Progress: {int(prog_val*100)}%")
    st.progress(prog_val)
    
    with st.expander("Details collected", expanded=False):
        for field, complete in prog_fields.items():
            icon = "✅" if complete else "⭕"
            st.write(f"{icon} {field}")
            
    # Conversation Management
    st.divider()
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Report", type="primary", use_container_width=True):
            if st.session_state.messages:
                full_log = "\n\n".join([f"[{m['role'].upper()}] {m['content']}" for m in st.session_state.messages])
                save_report_to_file(full_log)
            st.session_state.messages = []
            if os.path.exists(DRAFT_FILE):
                os.remove(DRAFT_FILE)
            st.rerun()
            
    with col2:
        if st.button("Undo Last", use_container_width=True):
            if len(st.session_state.messages) >= 1:
                st.session_state.messages.pop() 
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop() 
                save_draft(st.session_state.messages)
                st.rerun()

    # Past Reports
    with st.expander("📂 Past Reports"):
        reports = sorted(glob.glob(os.path.join(MEMORY_DIR, "*.txt")), reverse=True)[:5]
        if reports:
            selected_report = st.selectbox("Select report:", reports, format_func=lambda x: os.path.basename(x))
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("View"):
                    with open(selected_report, "r", encoding="utf-8") as f:
                        st.session_state['view_report_content'] = f.read()
            with col_b:
                with open(selected_report, "r", encoding="utf-8") as f:
                    txt_content = f.read()
                    pdf_bytes = create_pdf_report(txt_content)
                    st.download_button("PDF", pdf_bytes, file_name=os.path.basename(selected_report).replace('.txt', '.pdf'), mime='application/pdf')
            
            if 'view_report_content' in st.session_state:
                st.text_area("Content", st.session_state['view_report_content'], height=200)

        else:
            st.write("No reports found.")

    with st.expander("❓ Need Help?"):
        st.markdown("""
        **How to use:**
        1. Just type naturally.
        2. PocketPA will ask for missing details.
        3. Once done, it looks for the **<GENERATE_REPORT>** tag.
        4. Review the report and click 'Save'.
        """)
    
    st.divider()
    st.caption("v1.1.0 | Claude Opus")

# Main Chat Area

# Custom Header
st.markdown("""
<div class="main-header">
    <span class="status-badge">🟢 Online</span>
    <h1>PocketPA</h1>
    <p>Making care documentation effortless</p>
</div>
""", unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
             st.markdown(f'<div class="user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar="🛡️"):
            if "INCIDENT REPORT" in message["content"] and "BASIC INFORMATION" in message["content"]:
                st.markdown(f'<div class="report-box">{message["content"]}</div>', unsafe_allow_html=True)
                # Add PDF download for generated report in chat flow
                pdf_data = create_pdf_report(message["content"])
                st.download_button("📄 Download PDF", pdf_data, file_name="incident_report.pdf", mime="application/pdf", key=f"pdf_{len(message['content'])}")
            else:
                st.markdown(f'<div class="assistant-bubble">{message["content"]}</div>', unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Check text length
    if len(prompt) > 2000:
        st.error("Message too long. Please shorten it.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_draft(st.session_state.messages)
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)

        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("PocketPA is thinking..."):
                agents_ctx, skill_ctx = load_system_context()
                response_text = get_claude_response(st.session_state.messages, agents_ctx, skill_ctx)
                
                if "<GENERATE_REPORT>" in response_text:
                    clean_response = response_text.replace("<GENERATE_REPORT>", "").strip()
                    st.markdown(f'<div class="assistant-bubble">{clean_response}</div>', unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": clean_response})
                    
                    with st.spinner("Generating formal report..."):
                        report_content = generate_formal_report(st.session_state.messages)
                        
                        st.markdown("---")
                        st.markdown("### 📝 Generated Incident Report")
                        st.markdown(f'<div class="report-box">{report_content}</div>', unsafe_allow_html=True)
                        
                        # PDF Download Trigger
                        pdf_data = create_pdf_report(report_content)
                        st.download_button("📄 Download PDF", pdf_data, file_name="incident_report.pdf", mime="application/pdf")
                        
                        st.markdown(f'<div class="assistant-bubble">I\'ve prepared your incident report. Please review it carefully.</div>', unsafe_allow_html=True)
                        
                        combined_report_msg = f"{report_content}\n\nI've prepared your incident report. Please review it carefully."
                        st.session_state.messages.append({"role": "assistant", "content": combined_report_msg})
                else:
                    st.markdown(f'<div class="assistant-bubble">{response_text}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                save_draft(st.session_state.messages)
