# config.py
import json

USER_CSV_FIELDS = [
    ("id", lambda u: u.get("id", "")),
    ("firstName", lambda u: u.get("profile", {}).get("firstName", "")),
    ("lastName", lambda u: u.get("profile", {}).get("lastName", "")),
    ("email", lambda u: u.get("profile", {}).get("email", "")),
    ("login", lambda u: u.get("profile", {}).get("login", "")),
    ("status", lambda u: u.get("status", "")),
    ("created", lambda u: u.get("created", "")),
    ("lastLogin", lambda u: u.get("lastLogin", "")),
    ("lastUpdated", lambda u: u.get("lastUpdated", "")),
    ("passwordChanged", lambda u: u.get("passwordChanged", "")),
]

GROUP_LIST_CSV_FIELDS = [
    ("id", lambda g: g.get("id", "")),
    ("name", lambda g: g.get("profile", {}).get("name", "")),
    ("description", lambda g: g.get("profile", {}).get("description", "")),
    ("type", lambda g: g.get("type", "")),
    ("created", lambda g: g.get("created", "")),
    ("lastUpdated", lambda g: g.get("lastUpdated", "")),
    ("lastMembershipUpdated", lambda g: g.get("lastMembershipUpdated", "")),
]

GROUP_DETAIL_CSV_FIELDS = [
    ("id", lambda g: g.get("id", "")),
    ("name", lambda g: g.get("name", "")),
    ("description", lambda g: g.get("description", "")),
    ("created", lambda g: g.get("created", "")),
    ("lastUpdated", lambda g: g.get("lastUpdated", "")),
    ("objectClass", lambda g: g.get("objectClass", "")),
    ("type", lambda g: g.get("type", "")),
    ("user_count_url", lambda g: g.get("user_count_url", "")),
    ("apps_url", lambda g: g.get("apps_url", "")),
]

GROUP_APP_CSV_FIELDS = [
    ("id", lambda a: a.get("id", "")),
    ("label", lambda a: a.get("label", "")),
    ("status", lambda a: a.get("status", "")),
    ("name", lambda a: a.get("name", "")),
    ("lastUpdated", lambda a: a.get("lastUpdated", "")),
]

GROUP_USER_CSV_FIELDS = [
    ("id", lambda u: u.get("id", "")),
    ("status", lambda u: u.get("status", "")),
    ("created", lambda u: u.get("created", "")),
    ("lastLogin", lambda u: u.get("lastLogin", "")),
    ("type_id", lambda u: u.get("type", {}).get("id", "")),
    ("firstName", lambda u: u.get("profile", {}).get("firstName", "")),
    ("lastName", lambda u: u.get("profile", {}).get("lastName", "")),
    ("email", lambda u: u.get("profile", {}).get("email", "")),
    ("login", lambda u: u.get("profile", {}).get("login", "")),
]

# アプリケーション情報については、ネストした情報もJSON文字列として付与する
APP_CSV_FIELDS = [
    ("id", lambda a: a.get("id", "")),
    ("name", lambda a: a.get("name", "")),
    ("label", lambda a: a.get("label", "")),
    ("status", lambda a: a.get("status", "")),
    ("created", lambda a: a.get("created", "")),
    ("lastUpdated", lambda a: a.get("lastUpdated", "")),
    ("signOnMode", lambda a: a.get("signOnMode", "")),
    ("accessibility", lambda a: json.dumps(
        a.get("accessibility", {}), ensure_ascii=False)),
    ("visibility", lambda a: json.dumps(a.get("visibility", {}), ensure_ascii=False)),
    ("features", lambda a: json.dumps(a.get("features", []), ensure_ascii=False)),
    ("credentials", lambda a: json.dumps(
        a.get("credentials", {}), ensure_ascii=False)),
    ("settings", lambda a: json.dumps(a.get("settings", {}), ensure_ascii=False)),
]

APP_GROUP_CSV_FIELDS = [
    ("id", lambda g: g.get("id", "")),
    ("name", lambda g: g.get("profile", {}).get("name", "")),
    ("description", lambda g: g.get("profile", {}).get("description", "")),
    ("created", lambda g: g.get("created", "")),
    ("lastUpdated", lambda g: g.get("lastUpdated", "")),
]

DEVICE_CSV_FIELDS = [
    ("id", lambda d: d.get("id", "")),
    ("status", lambda d: d.get("status", "")),
    ("created", lambda d: d.get("created", "")),
    ("lastUpdated", lambda d: d.get("lastUpdated", "")),
    ("displayName", lambda d: d.get("profile", {}).get("displayName", "")),
    ("platform", lambda d: d.get("profile", {}).get("platform", "")),
    ("manufacturer", lambda d: d.get("profile", {}).get("manufacturer", "")),
    ("model", lambda d: d.get("profile", {}).get("model", "")),
    ("osVersion", lambda d: d.get("profile", {}).get("osVersion", "")),
    ("serialNumber", lambda d: d.get("profile", {}).get("serialNumber", "")),
    ("udid", lambda d: d.get("profile", {}).get("udid", "")),
    ("sid", lambda d: d.get("profile", {}).get("sid", "")),
    ("registered", lambda d: d.get("profile", {}).get("registered", "")),
    ("secureHardwarePresent", lambda d: d.get(
        "profile", {}).get("secureHardwarePresent", "")),
    ("diskEncryptionType", lambda d: d.get(
        "profile", {}).get("diskEncryptionType", "")),
    ("resourceDisplayName", lambda d: d.get(
        "resourceDisplayName", {}).get("value", "")),
]
