# FreeIPA Permissions & Read-Only Group Design

## Overview
FreeIPA (Identity, Policy, Audit) is Red Hat’s centralized identity and access management system. It provides LDAP directory services, Kerberos authentication, DNS, and integration with SSSD on Linux systems. Permissions are layered using **roles, privileges, and permissions** that map to **groups**.

At Charter/Spectrum scale, IAM teams standardize permissions using a **least privilege model**:
- **Permissions** = fine-grained rights (e.g., read user entries).
- **Privileges** = collections of permissions (e.g., “Read Users”).
- **Roles** = collections of privileges (e.g., “Read-Only Access Role”).
- **Groups** = users assigned to roles, inheriting all privileges.

---

## FreeIPA Permission Hierarchy
1. **Permission (atomic rights):**
   Controls access at the LDAP object/attribute level (search, read, write, add, delete).

2. **Privilege:**
   Groups multiple permissions for logical access control.

3. **Role:**
   Associates privileges into job-aligned access levels (admin, helpdesk, auditor, read-only).

4. **Group:**
   End-users are added here; groups are bound to roles.

---

## Steps to Create a Read-Only Group

### 1. Create a Read-Only Permission
```bash
ipa permission-add "Read Only Users" \
  --type=user \
  --attrs=uid,givenName,sn,cn,mail,memberOf \
  --rights=read \
  --bindtype=all
```

- `--type=user` restricts to user objects.
- `--rights=read` limits to read operations only.
- Adjust `--attrs` to define exactly which fields are visible.

### 2. Bundle Into a Privilege
```bash
ipa privilege-add "Read Only Privilege"
ipa privilege-add-permission "Read Only Privilege" --permissions="Read Only Users"
```

### 3. Create a Role for Read-Only Access
```bash
ipa role-add "Read Only Role"
ipa role-add-privilege "Read Only Role" --privileges="Read Only Privilege"
```

### 4. Create a Group for End Users
```bash
ipa group-add read-only-group --desc="Application Read Only Access Group"
ipa role-add-member "Read Only Role" --groups=read-only-group
```

### 5. Add Users
```bash
ipa group-add-member read-only-group --users=jdoe,asmith
```

---

## Validation
Test with an account in the group:
```bash
ldapsearch -x -D "uid=jdoe,cn=users,cn=accounts,dc=example,dc=com" \
  -W -b "cn=users,cn=accounts,dc=example,dc=com" uid
```

- You should see **user entries returned**.
- Modification attempts (`ldapmodify`) will fail with `insufficient access`.

---

## Practical Example at Spectrum
- **Use Case:** NOC engineers need to check user/device assignments but not alter them.
- **Group:** `noc-readonly-group`.
- **Privileges:** `Read Users`, `Read Hosts`, `Read HBAC Policies`.
- **Role:** `NOC Audit Role`.
- **Binding:** All NOC engineers are placed into this group via FreeIPA, then apps (ticketing, dispatch) query FreeIPA for group membership to enforce read-only views.

---

## Best Practices
1. **Principle of Least Privilege** – start with minimal attributes, expand as necessary.
2. **Separate Audit Role** – give auditors the same read-only role but log all access.
3. **App Integration** – enforce read-only at both FreeIPA and app level. For example, the app should map `read-only-group` → view-only UI.
4. **Lifecycle Automation** – tie group membership to HR events (hire/terminate) via automation (e.g., Ansible or IPA API).
5. **Testing** – always test roles with a dummy account before assigning to real users.

---

## Summary
- **Permissions** = atomic rights (read/write).
- **Privileges** = bundles of permissions.
- **Roles** = bundles of privileges.
- **Groups** = where you put users.
- To make a **read-only group**, you define `read` permissions, build them into a privilege, assign that to a role, then bind a group to the role.

This setup ensures users in the group can authenticate and view application data **without modification rights**.
