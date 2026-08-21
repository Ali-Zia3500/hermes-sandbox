#!/usr/bin/env python3
"""Fetch and print a random cat fact from the catfact.ninja API.

Uses only the Python standard library (urllib). Prints the fact to stdout.
"""
import json
import socket
import urllib.error
import urllib.request

API_URL = "https://catfact.ninja/fact"
TIMEOUT = 10  # seconds


def get_cat_fact(url=API_URL, timeout=TIMEOUT, headers=None):
    """Return a random cat fact from the API as a string.

    Raises:
        urllib.error.HTTPError: on an HTTP-level failure (e.g. 403/404/5xx).
        urllib.error.URLError: on connection/network problems.
        socket.timeout / TimeoutError: if the request times out.
        ValueError: if the response is not valid JSON or lacks a 'fact' field.
    """
    req_headers = {"User-Agent": "cat-fact/1.0 (stdlib)"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    data = json.loads(body)
    if "fact" not in data:
        raise ValueError("API response missing 'fact' field: %r" % (data,))
    return data["fact"]


def main():
    try:
        fact = get_cat_fact()
    except urllib.error.HTTPError as exc:
        print("Error: HTTP %s from %s" % (exc.code, exc.geturl()))
        return 1
    except (socket.timeout, TimeoutError) as exc:
        print("Error: request timed out after %s seconds" % TIMEOUT)
        return 1
    except urllib.error.URLError as exc:
        print("Error: network/connection failed: %s" % exc.reason)
        return 1
    except ValueError as exc:
        print("Error: invalid response from API: %s" % exc)
        return 1
    print(fact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
