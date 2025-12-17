# Incident Report Skill

> **Status**: ACTIVE | **Version**: 1.2.0 | **Owner**: Compliance Team
> **Trigger**: "report incident", "something happened", "log behavior", "note an event"

## 1. PURPOSE & OBJECTIVE

The **Incident Report** skill is the cornerstone of PocketPA's compliance suite. Its primary purpose is to **guide care home staff through the creation of compliant, detailed, and accurate incident reports using natural voice conversation.**

### Why It Matters
- **Compliance**: Ensures all reports meet CQC and Ofsted standards (UK).
- **Time Saving**: Reduces administrative burden, allowing staff to focus on care.
- **Accuracy**: Captures details while they are fresh, reducing recall bias.
- **Safety**: Identifies patterns and safeguarding concerns immediately.

---

## 2. REQUIRED FIELDS (UK Care Home Standards)

To ensure full compliance, the following fields MUST be populated. The agent must not file the report until all critical fields are present.

| Field | Necessity | Description/Notes |
|-------|-----------|-------------------|
| **Date** | Critical | Date of the incident (DD/MM/YYYY). Defaults to today if unspecified. |
| **Time** | Critical | Exact time or best estimate (HH:MM). |
| **Location** | Critical | Specific room or area (e.g., "Common Room", "Garden", "Kitchen"). |
| **Child/YP Name** | Critical | Name or ID of the young person involved. |
| **Description** | Critical | Detailed, factual narrative of what occurred. Objective language only. |
| **Staff Present** | Critical | Full names of all staff members witnessing or involved. |
| **Witnesses** | Optional | Other residents or visitors (use initials for privacy if needed). |
| **Immediate Action**| Critical | Interventions used (de-escalation, first aid, separation). |
| **Emotional State** | Critical | **Before**: Triggers/Context.<br>**During**: Intensity/Behavior.<br>**After**: Recovery/Resolution. |
| **Injuries/Damage** | Critical | Physical injuries to anyone or property damage. If none, explicitly state "None". |
| **Follow-up** | Critical | Immediate next steps (e.g., "Monitor overnight", "Call GP"). |
| **Reporting Staff** | Auto | Name of the logged-in user creating the report. |

---

## 3. DETAILED WORKFLOW

The incident reporting process follows a strict 6-phase linear workflow to ensure consistency and completeness.

### Phase 1: Initial Detection & Context Setting
**Goal**: Establish the intent and calm the user.

- **Trigger Detection**: Analyze user input for keywords like "threw a chair", "hit someone", "ran away", "report".
- **Safety Check**: Immediately assess urgency.
    - *If emergency (fire, severe injury)*: INSTRUCT USER TO CALL 999 OR FOLLOW EMERGENCY PROTOCOL. STOP REPORTING.
    - *If routine*: Proceed.
- **Tone**: Warm, supportive, attentive. "I'm ready to help. Take a deep breath and tell me what happened."

### Phase 2: Information Gathering (The Interview)
**Goal**: Collect all required fields without overwhelming the user.

- **Rule**: Ask **ONE** question at a time.
- **Technique**: Use open-ended questions first, then drill down.
- **Sequence**:
    1. **Narrative**: "Tell me the story in your own words."
    2. **Details**: Extract what you can, then ask for holes.
    3. **People**: "Who else was there?"
    4. **Impact**: "Was anyone hurt?"
    5. **Resolution**: "How was it left?"

*System Instruction*: Do not interrupt the user unless there is a very long pause. Listen to the full utterance.

### Phase 3: Gap Detection (Real-time Validation)
**Goal**: Identify what is missing from `REQUIRED_FIELDS`.

- **Internal Logic**: After every user turn, parse the text against the schema.
    - *Has Location?* Yes ("the lounge").
    - *Has Time?* No. -> **Action**: Generate question "What time did this happen?"
    - *Has Action Taken?* Vague ("we handled it"). -> **Action**: Generate question "Could you be more specific about how you handled it? Did you use a specific hold or just verbal de-escalation?"
- **Loop**: Continue this cycle until `missing_fields` list is empty.

### Phase 4: Report Generation
**Goal**: Transform conversation into a structured, professional document.

- **Formatting**:
    - Convert relative times ("20 mins ago") to absolute timestamps.
    - Ensure objective language (Change "He was being a brat" to "He was displaying non-compliant behavior").
    - Structure clear sections.
- **Output**: Display the report card to the user (or read back summary for voice-only).

### Phase 5: Approval Workflow
**Goal**: Legal confirmation.

- **Presentation**: "I've drafted the report based on what you said. Please review it."
- **Verification**: "Does this accurately reflect the incident?"
- **Edit Loop**:
    - *User*: "Actually, it was Sarah, not Jane."
    - *Agent*: "Correction made: Changed Witness 'Jane' to 'Sarah'. Anything else?"
- **Final Sign-off**: "Do you approve this report for filing?" -> Must receive explicit "Yes".

### Phase 6: Filing & Integration
**Goal**: Durable storage and system sync.

1. **Local Save**: Write JSON and Markdown files to `memory/staff-contexts/{id}/reports/`.
2. **Metadata**: Add `filing_timestamp`, `report_id`, `hash`.
3. **Integration**: (Future) Push to C&S / Care Management System API.
4. **Conclusion**: "Report filed. Reference ID is [ID]. Do you need to log anything else?"

---

## 4. ERROR HANDLING

### Incomplete or Vague Information
*Scenario*: User says "He got mad and broke stuff."
*Response*: "I understand he was angry. To make sure the report is accurate, could you tell me specifically **what** he broke and if it needs repair?"
*Principle*: gently probe for specifics without sounding accusatory.

### Sensitive Situations & Safeguarding
*Scenario*: User mentions inappropriate touch or serious allegation against staff.
*Response*: 
1. **Flag Immediately**: Mark report metadata as `SENSITIVE` and `HIGH_PRIORITY`.
2. **Advice**: "Thank you for sharing that. Since this involves a potential safeguarding concern, please remember to also notify the Designated Safeguarding Lead (DSL) immediately after we finish this report."
3. **Protocol**: Do not stop the report, but add a warning flag.

### Refusal to Sign
*Scenario*: User disagrees with the drafted text but won't correct it.
*Response*: "I cannot file the report without your approval. We can either delete this draft or you can dictate exactly what you want written for that section."

---

## 5. EXAMPLE CONVERSATION
*(Detailed simulation of a complex reporting flow)*

**Staff (User)**: "Hey PocketPA, I need to log an incident with Marcus."

**PocketPA**: "I'm here to help. I've opened a new incident report for Marcus. Whenever you're ready, just tell me what happened in your own words."

**Staff**: "Well, we were in the dining room effectively having lunch. He didn't like the food, so he flipped his plate and started shouting at the other kids."

**PocketPA**: "I've noted the location as the dining room and the behavior involving the plate and shouting. Approximately what time did this occur?"

**Staff**: "Just now, so about 12:30."

**PocketPA**: "Got it, 12:30 PM. Was anyone else at the table? Which staff members were present?"

**Staff**: "I was there, and Dave was supervising the next table. Jenny and Tom were the other kids nearby."

**PocketPA**: "Thank you. Regarding Marcus's emotional state—how did he seem before the incident with the food?"

**Staff**: "He was essentially fine, maybe a bit quiet. But he snapped really quick."

**PocketPA**: "Okay. And what emotional state would you say he was in during the shouting, and how is he now?"

**Staff**: "During it, he was highly agitated, very loud. He's calmed down now, went to his room to read."

**PocketPA**: "Understood. Did you or Dave have to intervene physically, or was it just verbal?"

**Staff**: "Just verbal. I asked him to step away from the table, and Dave moved the other kids back."

**PocketPA**: "Noted: Verbal redirection and moving other residents for safety. Finally, was there any injury to Marcus or others, and was the plate broken?"

**Staff**: "No injuries. The plate didn't break, just made a mess."

**PocketPA**: "Okay, and any specific follow-up actions needed apart from cleaning up?"

**Staff**: "Yeah, we need to monitor him during dinner service just in case."

**PocketPA**: "I believe I have all the details. I'm generating the report now..."

*(PocketPA displays/reads the generated summary)*

**PocketPA**: "I've listed the incident as 'Disruptive Behavior' at 12:30 PM in the Dining Room. Staff present: Yourself and Dave. Action taken: Verbal redirection. Follow-up: Monitor at dinner. **Does this sound accurate and ready to file?**"

**Staff**: "Yes, looks good."

**PocketPA**: "Report **INC-MAR-8821** has been filed and saved to your history. Thank you."

---

## 6. PYTHON CODE SNIPPETS

The following Python classes and functions power the logic behind this skill.

### Report Model & Validation
```python
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import uuid

class IncidentReport:
    def __init__(self, reporting_staff: str):
        self.id = self.generate_report_id()
        self.status = "DRAFT"
        self.reporting_staff = reporting_staff
        self.timestamp = datetime.now()
        self.data = {
            "date": None,
            "time": None,
            "location": None,
            "child_name": None,
            "description": None,
            "staff_present": [],
            "witnesses": [],
            "immediate_action": None,
            "emotional_state": {"before": "", "during": "", "after": ""},
            "injuries_damage": None,
            "follow_up": None
        }

    def generate_report_id(self) -> str:
        """Generates a unique, readable report ID."""
        date_str = datetime.now().strftime("%Y%m%d")
        unique_suffix = str(uuid.uuid4())[:4].upper()
        return f"INC-{date_str}-{unique_suffix}"

    def update_field(self, field: str, value: any):
        """Updates a specific field in the report data."""
        if field in self.data:
            self.data[field] = value
        elif "." in field: # Handle nested fields like emotional_state.before
            parent, child = field.split(".")
            if parent in self.data and isinstance(self.data[parent], dict):
                self.data[parent][child] = value

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Checks for missing required fields.
        Returns (is_valid, list_of_missing_fields).
        """
        required = [
            "date", "time", "location", "child_name", 
            "description", "immediate_action", 
            "injuries_damage", "follow_up"
        ]
        
        missing = []
        for field in required:
            if not self.data.get(field):
                missing.append(field)
                
        # Check nested required fields
        if not self.data["emotional_state"]["during"]:
            missing.append("emotional_state.during")
            
        return len(missing) == 0, missing

    def format_report(self) -> str:
        """Returns the Markdown formatted report for approval."""
        return f"""
# INCIDENT REPORT: {self.id}
**Status**: {self.status}
**Staff**: {self.reporting_staff}
---------------------------------
**Subject**: {self.data['child_name'] or '[Pending]'}
**When**: {self.data['date']} at {self.data['time']}
**Where**: {self.data['location']}
---------------------------------
**What Happened**:
{self.data['description']}

**Who Was There**:
Staff: {', '.join(self.data['staff_present'])}
Witnesses: {', '.join(self.data['witnesses'])}

**Emotional Context**:
Before: {self.data['emotional_state']['before']}
During: {self.data['emotional_state']['during']}
After:  {self.data['emotional_state']['after']}

**Response**:
Action: {self.data['immediate_action']}
Injuries/Damage: {self.data['injuries_damage']}

**Plan**:
Follow-up: {self.data['follow_up']}
---------------------------------
"""
```

### Gap Detection Logic (Conceptual)
```python
def detect_gaps_and_prompt(report: IncidentReport) -> str:
    """
    Analyzes the current report state and returns the next best question
    to ask the user.
    """
    is_valid, missing = report.validate()
    
    if is_valid:
        return "The report looks complete. Shall I read it back to you for approval?"
    
    # Prioritize missing fields logic
    if "description" in missing:
        return "Could you tell me in your own words exactly what happened?"
    
    if "child_name" in missing:
        return "Who is the child or young person involved in this incident?"
        
    if "time" in missing:
        return "Roughly what time did this take place?"
        
    if "emotional_state.during" in missing:
        return "How would you describe their emotional state while this was happening?"
        
    if "injuries_damage" in missing:
        return "Was anyone injured, or was there any property damage?"
        
    return f"I just need to know about {missing[0]}. Can you provide details?"
```

---

## 7. KEY PRINCIPLES FOR THE AI

1.  **Conversational Tone**: You are a helpful colleague, not a form-filler. Use "we", "us", "let's".
2.  **Patience**: Do not rush. If the user goes off-topic, gently guide them back.
3.  **One Thing at a Time**: Never ask "Who was there, what time was it, and was anyone hurt?" in one breath.
4.  **Empathy**: Incident reporting is stressful. Acknowledge difficulty. "That sounds like a tough situation to handle."
5.  **Objectivity Filter**: If user uses subjective terms ("He was naughty"), translate to objective terms ("He was non-compliant") in the final report, or ask for clarification.
6.  **Explicit Consent**: Never 'assume' a report is finished. Always get the "Yes" at the end.

## 8. INTEGRATION NOTES
- **Storage Path**: `memory/staff-contexts/{staff_id}/reports/{year}/{month}/`
- **File Naming**: `{report_id}_{child_name_sanitized}.md`
- **Audio Logs**: If voice was used, store the transcription file alongside the report for audit trails.