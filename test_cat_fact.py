#!/usr/bin/env python3
"""Tests for cat_fact.py using only the standard library (unittest).

Covers: happy-path parsing, missing 'fact' field, HTTP errors, network/timeout
errors, and the main() exit-code paths. No network calls are made; urllib is
patched in-process.
"""
import json
import socket
import unittest
import urllib.error
import urllib.request
from email.message import Message
from unittest import mock

import cat_fact


def _resp(body=b"", status=200, url="https://catfact.ninja/fact"):
    resp = mock.MagicMock()
    resp.read.return_value = body
    resp.getcode.return_value = status
    resp.geturl.return_value = url
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


class GetCatFactTests(unittest.TestCase):
    def test_returns_fact_on_valid_response(self):
        payload = json.dumps({"fact": "Cats have 32 muscles in each ear."})
        with mock.patch.object(urllib.request, "urlopen", return_value=_resp(payload.encode())):
            self.assertEqual(cat_fact.get_cat_fact(), "Cats have 32 muscles in each ear.")

    def test_raises_value_error_when_fact_missing(self):
        payload = json.dumps({"length": 42})
        with mock.patch.object(urllib.request, "urlopen", return_value=_resp(payload.encode())):
            with self.assertRaises(ValueError):
                cat_fact.get_cat_fact()

    def test_raises_http_error_on_bad_status(self):
        err = urllib.error.HTTPError(
            url="https://catfact.ninja/fact", code=403, msg="Forbidden",
            hdrs=Message(), fp=mock.MagicMock(read=mock.MagicMock(return_value=b"")),
        )
        with mock.patch.object(urllib.request, "urlopen", side_effect=err):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                cat_fact.get_cat_fact()
            self.assertEqual(ctx.exception.code, 403)

    def test_propagates_url_error(self):
        err = urllib.error.URLError(socket.gaierror("no host"))
        with mock.patch.object(urllib.request, "urlopen", side_effect=err):
            with self.assertRaises(urllib.error.URLError):
                cat_fact.get_cat_fact()

    def test_propagates_timeout(self):
        with mock.patch.object(urllib.request, "urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaises(socket.timeout):
                cat_fact.get_cat_fact()


class MainTests(unittest.TestCase):
    def _patch_urlopen(self, return_value=None, side_effect=None):
        return mock.patch.object(urllib.request, "urlopen", return_value=return_value, side_effect=side_effect)

    def test_main_prints_fact_and_returns_zero(self):
        payload = json.dumps({"fact": "A cat has 32 muscles in each ear."}).encode()
        with self._patch_urlopen(return_value=_resp(payload)):
            with mock.patch("builtins.print") as p:
                rc = cat_fact.main()
        self.assertEqual(rc, 0)
        p.assert_called_once_with("A cat has 32 muscles in each ear.")

    def test_main_http_error_returns_one(self):
        err = urllib.error.HTTPError(
            url="https://catfact.ninja/fact", code=500, msg="Server Error",
            hdrs=Message(), fp=mock.MagicMock(read=mock.MagicMock(return_value=b"")),
        )
        with self._patch_urlopen(side_effect=err):
            with mock.patch("builtins.print") as p:
                rc = cat_fact.main()
        self.assertEqual(rc, 1)
        args, _ = p.call_args
        self.assertIn("HTTP 500", args[0])

    def test_main_url_error_returns_one(self):
        err = urllib.error.URLError(Exception("connection refused"))
        with self._patch_urlopen(side_effect=err):
            with mock.patch("builtins.print") as p:
                rc = cat_fact.main()
        self.assertEqual(rc, 1)
        args, _ = p.call_args
        self.assertIn("network/connection failed", args[0])

    def test_main_timeout_returns_one(self):
        with self._patch_urlopen(side_effect=socket.timeout("timed out")):
            with mock.patch("builtins.print") as p:
                rc = cat_fact.main()
        self.assertEqual(rc, 1)
        args, _ = p.call_args
        self.assertIn("timed out", args[0])


if __name__ == "__main__":
    unittest.main()
