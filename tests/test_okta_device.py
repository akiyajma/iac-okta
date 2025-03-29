import json


class DummyResponse:
    def __init__(self, json_data, status_code, headers=None):
        self._json = json_data
        self.status_code = status_code
        self.headers = headers or {}
        self.text = json.dumps(json_data)

    def json(self):
        return self._json


def test_get_okta_all_devices(monkeypatch, tmp_path):
    """
    Test retrieving all devices.
    This test mocks the requests.get call to return a dummy devices list,
    and verifies that a CSV file is created in the output folder.
    """
    monkeypatch.chdir(tmp_path)

    dummy_devices = [
        {
            "id": "device1",
            "status": "ACTIVE",
            "created": "2020-01-01T00:00:00.000Z",
            "lastUpdated": "2020-01-02T00:00:00.000Z",
            "profile": {
                "displayName": "Device One",
                "platform": "WINDOWS",
                "manufacturer": "Manufacturer1",
                "model": "Model1",
                "osVersion": "10.0",
                "serialNumber": "SN123",
                "udid": "UDID123",
                "sid": "SID123",
                "registered": True,
                "secureHardwarePresent": False,
                "diskEncryptionType": "NONE"
            },
            "resourceDisplayName": {"value": "Device One"}
        }
    ]

    def dummy_get(url, headers):
        return DummyResponse(dummy_devices, 200, headers={})

    monkeypatch.setattr("okta_device.requests.get", dummy_get)

    from okta_device import get_okta_all_devices

    devices = get_okta_all_devices("dummy_token", "https://example.okta.com")
    assert devices == dummy_devices

    output_csv = tmp_path / "output" / "devices.csv"
    assert output_csv.exists()
    content = output_csv.read_text(encoding="utf-8")
    assert "device1" in content


def test_get_okta_device_detail(monkeypatch, tmp_path):
    """
    Test retrieving detailed information for a specific device.
    This test mocks the requests.get call to return a dummy device detail,
    and verifies that a CSV file is created with the expected content.
    """
    monkeypatch.chdir(tmp_path)

    dummy_device_detail = {
        "id": "device_detail_1",
        "status": "ACTIVE",
        "created": "2020-11-03T21:47:01.000Z",
        "lastUpdated": "2020-11-03T23:46:27.000Z",
        "profile": {
            "displayName": "Device Detail One",
            "platform": "WINDOWS",
            "manufacturer": "International Corp",
            "model": "VMware7,1",
            "osVersion": "10.0.18362",
            "serialNumber": "56 4d 4f 95 74 c5 d3 e7-fc 3a 57 9c c2 f8 5d ce",
            "udid": "954F4D56-C574-E7D3-FC3A-579CC2F85DCE",
            "sid": "S-1-5-21-3992267483-1860856704-2413701314-500",
            "registered": True,
            "secureHardwarePresent": False,
            "diskEncryptionType": "NONE"
        },
        "resourceDisplayName": {"value": "Device Detail One"}
    }

    def dummy_get(url, headers):
        return DummyResponse(dummy_device_detail, 200)

    monkeypatch.setattr("okta_device.requests.get", dummy_get)

    from okta_device import get_okta_device_detail

    detail = get_okta_device_detail(
        "dummy_token", "https://example.okta.com", "device_detail_1")
    assert detail is not None
    output_csv = tmp_path / "output" / "device_detail_device_detail_1.csv"
    assert output_csv.exists()
    content = output_csv.read_text(encoding="utf-8")
    assert "Device Detail One" in content
