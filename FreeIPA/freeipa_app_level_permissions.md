# Application-Level Permissions with FreeIPA

## What Are App-Level Permissions?
- **FreeIPA’s Role** → Provides identity (who you are) and group membership (what high-level role you belong to).
- **App-Level Permissions** → Translate those group memberships into what you can actually do **inside the application** (UI and API enforcement).

This creates a **two-step authorization chain**:
1. **Authentication + Group Mapping (FreeIPA)**  
   - FreeIPA says: “`jdoe` is in `read-only-group`.”
2. **App Enforcement**  
   - The app maps `read-only-group` → “Show dashboard, but disable all write buttons/API calls.”

---

## Why Both Levels Matter
- **Directory enforcement** (FreeIPA) → Prevents LDAP writes, keeps central security tight.  
- **App enforcement** → Prevents accidental or malicious actions in the UI/API.  
- At Spectrum scale, **both layers are mandatory** for compliance and SOC2 auditing.  

---

## Example: Read-Only User in an Application

### Step 1: Group Assignment in FreeIPA
We already created `read-only-group` in FreeIPA. `jdoe` is a member.

```bash
ipa group-add-member read-only-group --users=jdoe
```

### Step 2: Application Checks Group Membership
When `jdoe` logs into the app (via LDAP/Kerberos/SSO):
- App queries FreeIPA (using `ldapsearch` or SSSD cache).
- App sees `memberOf=read-only-group`.

**Python Pseudo-Code:**
```python
if "read-only-group" in user_groups:
    user_role = "read_only"
else:
    user_role = "standard"
```

### Step 3: Enforce Permissions in the App
Inside the app:
- Define permissions as code (or config).
- Assign **read-only role** to certain UI and API endpoints.

**Example: Flask App**
```python
from flask import Flask, jsonify, request

app = Flask(__name__)

# Simulated user session
current_user = {"username": "jdoe", "role": "read_only"}

@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "GET":
        return jsonify({"users": ["jdoe", "asmith", "bjones"]})
    if current_user["role"] == "read_only":
        return jsonify({"error": "Permission denied"}), 403
    return jsonify({"message": "User added"})
```

- `GET /users` works for everyone.  
- `POST /users` fails with **403 Permission denied** for read-only users.  

### Step 4: UI Enforcement
Frontend must also enforce read-only restrictions.  

**Example: React**
```jsx
{userRole !== "read_only" && <button>Add User</button>}
```

---

## YAML Config Example
Applications can use external config to define roles:

```yaml
roles:
  read_only:
    description: "View data only, no modifications"
    permissions:
      - view_users
      - export_reports

  standard_user:
    description: "Regular user with edit access"
    permissions:
      - view_users
      - edit_users
      - export_reports
```

Your application logic then reads the config and checks if the current user’s role allows a given action.

---

## Practical Spectrum Example
- **NOC Tool**: Engineers can see network device status, logs, and alarms.  
- **Read-only users** (interns, auditors) → can view alarms, export logs, but cannot acknowledge or clear alarms.  
- **Implementation**:
  - FreeIPA `noc-readonly-group`.  
  - App maps `noc-readonly-group` → `viewer` role.  
  - Viewer role only gets access to `/view/*` routes, not `/ack/*` or `/config/*`.  

---

## Best Practices
1. **Always double-enforce** (FreeIPA + App).  
2. **Config-driven roles** in the app (YAML/JSON instead of hardcoding).  
3. **Audit logs** → log every denied action attempt.  
4. **Fail closed** → if app can’t determine role, default to no write access.  
5. **UI + API alignment** → never rely only on UI hiding; enforce on the backend too.  

---

✅ This ensures your read-only group has **zero write capability**:  
- FreeIPA prevents LDAP writes.  
- App prevents API/UI writes.  
- Auditors see clear evidence of enforcement.
