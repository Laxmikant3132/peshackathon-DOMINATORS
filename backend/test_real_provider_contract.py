import unittest
from services.intel_providers import (
    is_publicly_routable_ip,
    extract_all_ips_from_received,
    identify_earliest_public_ip,
    IPGeolocationProvider
)
from unittest.mock import patch, MagicMock
import requests

class TestRealProviderIntegration(unittest.TestCase):
    def test_live_ipinfo_with_token(self):
        # Test simulated valid provider response matching real IPinfo structure
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ip": "1.1.1.1",
            "city": "Brisbane",
            "region": "Queensland",
            "country": "AU",
            "loc": "-27.4679,153.0281",
            "org": "AS13335 Cloudflare, Inc.",
            "timezone": "Australia/Brisbane",
            "privacy": {
                "vpn": False,
                "proxy": False,
                "tor": False,
                "relay": True,
                "hosting": True
            }
        }
        with patch.dict("os.environ", {"IPINFO_TOKEN": "real_mock_token"}):
            with patch("requests.get", return_value=mock_resp):
                geo = IPGeolocationProvider.get_geolocation("1.1.1.1")
                self.assertEqual(geo["provider_state"], "AVAILABLE")
                self.assertEqual(geo["ip"], "1.1.1.1")
                self.assertEqual(geo["country"], "AU")
                self.assertEqual(geo["city"], "Brisbane")
                self.assertEqual(geo["asn"], "AS13335")
                self.assertEqual(geo["isp"], "Cloudflare, Inc.")
                self.assertIn("Mail Relay / CDN", geo["infrastructure_type"])
                self.assertIn("Cloud Hosting", geo["infrastructure_type"])
                self.assertIn("Notice: This IP belongs to a VPN, proxy, Tor exit node, cloud host, CDN, or mail relay.", geo["infrastructure_notice"])
                self.assertEqual(geo["latitude"], -27.4679)
                self.assertEqual(geo["longitude"], 153.0281)
                self.assertEqual(geo["source"], "IPinfo")
                self.assertIn("disclaimer", geo)

if __name__ == "__main__":
    unittest.main()
