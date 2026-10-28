import unittest
import os
from unittest.mock import patch, MagicMock
from services.intel_providers import (
    is_publicly_routable_ip,
    extract_all_ips_from_received,
    identify_earliest_public_ip,
    IPGeolocationProvider
)
import requests

class TestIPGeolocationForensics(unittest.TestCase):

    def test_public_ipv4(self):
        """Test public IPv4 addresses are accepted as routable."""
        self.assertTrue(is_publicly_routable_ip("8.8.8.8"))
        self.assertTrue(is_publicly_routable_ip("1.1.1.1"))
        self.assertTrue(is_publicly_routable_ip("93.184.216.34"))

    def test_public_ipv6(self):
        """Test public IPv6 addresses are accepted as routable."""
        self.assertTrue(is_publicly_routable_ip("2606:4700:4700::1111"))
        self.assertTrue(is_publicly_routable_ip("2001:4860:4860::8888"))

    def test_private_ip(self):
        """Test RFC 1918 and loopback IPv4 addresses are filtered out."""
        self.assertFalse(is_publicly_routable_ip("127.0.0.1"))
        self.assertFalse(is_publicly_routable_ip("10.0.0.1"))
        self.assertFalse(is_publicly_routable_ip("172.16.5.4"))
        self.assertFalse(is_publicly_routable_ip("192.168.1.100"))
        self.assertFalse(is_publicly_routable_ip("::1"))

    def test_reserved_and_documentation_ip(self):
        """Test RFC 5737 / RFC 3849 / carrier-grade NAT documentation and reserved IPs are filtered out."""
        self.assertFalse(is_publicly_routable_ip("192.0.2.1"))     # TEST-NET-1
        self.assertFalse(is_publicly_routable_ip("198.51.100.22")) # TEST-NET-2
        self.assertFalse(is_publicly_routable_ip("203.0.113.77"))  # TEST-NET-3
        self.assertFalse(is_publicly_routable_ip("2001:db8::1"))   # IPv6 doc
        self.assertFalse(is_publicly_routable_ip("100.64.0.1"))    # Shared Address Space
        self.assertFalse(is_publicly_routable_ip("not-an-ip"))

    def test_extract_all_ips_from_received(self):
        """Test extraction of mixed IPv4 and IPv6 from Received headers."""
        headers = [
            "from mail.example.com (mail.example.com [192.0.2.1]) by mx.google.com with ESMTPS id 123",
            "from [2606:4700:4700::1111] (unknown [8.8.8.8]) by relay.example.com"
        ]
        ips = extract_all_ips_from_received(headers)
        self.assertIn("192.0.2.1", ips)
        self.assertIn("2606:4700:4700::1111", ips)
        self.assertIn("8.8.8.8", ips)

    def test_identify_earliest_public_ip(self):
        """Test finding the earliest (originating) public IP from multi-hop headers."""
        headers = [
            # Top hop (destination MX receiving from internal or intermediate relay)
            "from relay.company.com (10.0.0.5) by mx.company.com",
            # Intermediate relay receiving from public MTA
            "from mail.sender.com (1.1.1.1) by relay.company.com",
            # Earliest origin hop (public IP connecting from an internal private IP)
            "from user-pc (192.168.1.50) by mail.sender.com (93.184.216.34)"
        ]
        earliest = identify_earliest_public_ip(headers)
        # Should identify 93.184.216.34 because it is the earliest public IP in the chain
        self.assertEqual(earliest, "93.184.216.34")

    def test_identify_earliest_public_ip_none_when_all_private(self):
        """Test returns None when chain contains only private/doc IPs."""
        headers = [
            "from relay1 (10.0.0.1) by relay2 (192.168.1.1)",
            "from client (127.0.0.1) by relay1 (192.0.2.1)"
        ]
        earliest = identify_earliest_public_ip(headers)
        self.assertIsNone(earliest)

    def test_missing_api_key(self):
        """Test returns UNAVAILABLE without fabricating data when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("IPINFO_TOKEN", None)
            os.environ.pop("IPINFO_API_KEY", None)
            res = IPGeolocationProvider.get_geolocation("8.8.8.8")
            self.assertEqual(res["provider_state"], "UNAVAILABLE")
            self.assertIn("IPINFO_TOKEN missing", res["error"])
            self.assertIn("disclaimer", res)

    def test_provider_timeout(self):
        """Test handles network timeouts gracefully by returning UNAVAILABLE."""
        with patch.dict(os.environ, {"IPINFO_TOKEN": "test_token"}):
            with patch("requests.get", side_effect=requests.exceptions.Timeout):
                res = IPGeolocationProvider.get_geolocation("8.8.8.8")
                self.assertEqual(res["provider_state"], "UNAVAILABLE")
                self.assertIn("timed out", res["error"])

    def test_valid_provider_response(self):
        """Test parsing a complete, valid IPinfo response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ip": "8.8.8.8",
            "city": "Mountain View",
            "region": "California",
            "country": "US",
            "loc": "37.4056,-122.0775",
            "org": "AS15169 Google LLC",
            "timezone": "America/Los_Angeles",
            "privacy": {
                "vpn": False,
                "proxy": False,
                "tor": False,
                "relay": False,
                "hosting": True
            }
        }
        with patch.dict(os.environ, {"IPINFO_TOKEN": "test_token"}):
            with patch("requests.get", return_value=mock_resp):
                res = IPGeolocationProvider.get_geolocation("8.8.8.8")
                self.assertEqual(res["provider_state"], "AVAILABLE")
                self.assertEqual(res["ip"], "8.8.8.8")
                self.assertEqual(res["city"], "Mountain View")
                self.assertEqual(res["region"], "California")
                self.assertEqual(res["country"], "US")
                self.assertEqual(res["latitude"], 37.4056)
                self.assertEqual(res["longitude"], -122.0775)
                self.assertEqual(res["asn"], "AS15169")
                self.assertEqual(res["isp"], "Google LLC")
                self.assertTrue(res["is_hosting"])
                self.assertIn("Cloud Hosting", res["infrastructure_type"])
                self.assertIn("disclaimer", res)
                self.assertIn("infrastructure_notice", res)

    def test_incomplete_provider_response(self):
        """Test handles partial provider responses without fabricating missing fields."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ip": "8.8.8.8",
            # city, region, loc, org missing
            "country": "US"
        }
        with patch.dict(os.environ, {"IPINFO_TOKEN": "test_token"}):
            with patch("requests.get", return_value=mock_resp):
                res = IPGeolocationProvider.get_geolocation("8.8.8.8")
                self.assertEqual(res["provider_state"], "AVAILABLE")
                self.assertEqual(res["country"], "US")
                self.assertIsNone(res["city"])
                self.assertIsNone(res["region"])
                self.assertIsNone(res["latitude"])
                self.assertIsNone(res["longitude"])
                self.assertIsNone(res["asn"])

if __name__ == "__main__":
    unittest.main()
